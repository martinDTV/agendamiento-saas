import re
import logging

import httpx
from django.conf import settings


logger = logging.getLogger(__name__)


def _parse_section(raw: str, label: str, max_index: int, max_picks: int = 3) -> list[int]:
    """
    Find a section like 'SERVICIOS: 1, 3' in `raw` and return up to `max_picks`
    valid 1-based indices in [1, max_index]. Falls back to scanning the whole
    response if the labelled section is missing.
    """
    pattern = rf'{label}\s*[:\-]?\s*([0-9,\s]+)'
    match = re.search(pattern, raw, flags=re.IGNORECASE)
    haystack = match.group(1) if match else raw
    seen, result = set(), []
    for token in re.findall(r'\b\d+\b', haystack):
        n = int(token)
        if 1 <= n <= max_index and n not in seen:
            seen.add(n)
            result.append(n)
            if len(result) >= max_picks:
                break
    return result


def suggest_booking(
    reason: str,
    services: list[dict],
    doctors: list[dict],
) -> tuple[list[str], list[str]]:
    """
    Ask Ollama to pick relevant services AND doctors for a consultation reason.
    Returns (service_ids, doctor_ids) — both lists may be empty on failure.

    Strategy: numbered lists for both, single prompt, parse two labelled sections.
    LLMs are unreliable copying UUIDs, so we map indices server-side.
    """
    if not services and not doctors:
        return [], []

    service_list = '\n'.join(
        f'{i + 1}. {s["name"]} — {s.get("description", "") or "Consulta médica"}'
        for i, s in enumerate(services)
    )
    doctor_list = '\n'.join(
        f'{i + 1}. {d["full_name"]} — {d.get("specialty") or "Medicina General"}'
        for i, d in enumerate(doctors)
    )

    prompt = (
        f'Eres un asistente médico. Un paciente describe su motivo de consulta:\n'
        f'"{reason}"\n\n'
        f'Servicios disponibles (numerados):\n{service_list or "(ninguno)"}\n\n'
        f'Doctores disponibles (numerados):\n{doctor_list or "(ninguno)"}\n\n'
        f'Sugiere los más adecuados para este motivo. Responde EXACTAMENTE en este formato, sin explicar:\n'
        f'SERVICIOS: <números separados por coma, máximo 2>\n'
        f'DOCTORES: <números separados por coma, máximo 2>\n\n'
        f'Ejemplo:\n'
        f'SERVICIOS: 1, 3\n'
        f'DOCTORES: 2\n\n'
        f'Respuesta:'
    )

    try:
        resp = httpx.post(
            f'{settings.OLLAMA_BASE_URL}/api/generate',
            json={'model': settings.OLLAMA_MODEL_TEXT, 'prompt': prompt, 'stream': False},
            timeout=settings.OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json().get('response', '')
        logger.info('Ollama raw response: %s', raw[:500])

        service_idx = _parse_section(raw, 'SERVICIOS', len(services), max_picks=2)
        doctor_idx = _parse_section(raw, 'DOCTORES', len(doctors), max_picks=2)

        return (
            [str(services[i - 1]['id']) for i in service_idx],
            [str(doctors[i - 1]['id']) for i in doctor_idx],
        )
    except Exception as exc:
        logger.warning('Ollama suggestion failed: %s', exc)
        return [], []


# Backwards-compat alias used by older code paths.
def suggest_services(reason: str, services: list[dict]) -> list[str]:
    service_ids, _ = suggest_booking(reason, services, [])
    return service_ids


def summarize_conversation_title(messages: list[dict]) -> str:
    """
    Genera un título corto (5-8 palabras) que resume el tema central de una
    conversación de soporte. Recibe lista de {sender, content}. Devuelve string.

    Útil al cerrar una conversación: el admin después puede ver de un vistazo
    de qué se habló sin tener que leerla entera.
    """
    if not messages:
        return ''

    transcript = '\n'.join(
        f'{m.get("sender", "?").upper()}: {m.get("content", "")}'
        for m in messages[-20:]  # últimos 20 mensajes alcanzan
    )

    prompt = (
        f'Lee la siguiente conversación entre un visitante y un agente de soporte.\n\n'
        f'{transcript}\n\n'
        f'Generá UN título descriptivo de 5 a 8 palabras (en español) que resuma el TEMA CENTRAL '
        f'de la conversación. Sin comillas, sin explicación, solo el título.\n'
        f'Ejemplos: "Reagendamiento de cita por enfermedad", "Consulta sobre métodos de pago", '
        f'"Problema técnico con login del paciente".\n\n'
        f'Título:'
    )

    try:
        resp = httpx.post(
            f'{settings.OLLAMA_BASE_URL}/api/generate',
            json={'model': settings.OLLAMA_MODEL_TEXT, 'prompt': prompt, 'stream': False},
            timeout=settings.OLLAMA_TIMEOUT * 2,
        )
        resp.raise_for_status()
        raw = (resp.json().get('response') or '').strip()
        # Limpiar comillas u otros adornos que el modelo a veces agrega
        title = raw.split('\n')[0].strip().strip('"').strip("'").strip('.')
        # Truncar a 120 chars (límite del modelo Conversation.title)
        return title[:120] if title else ''
    except Exception as exc:
        logger.warning('Ollama title generation failed: %s', exc)
        return ''


def suggest_agent_reply(
    conversation_messages: list[dict],
    tenant_context: dict,
) -> str:
    """
    Genera una sugerencia de respuesta para que un AGENTE de soporte pueda
    enviar al visitante. Lee la última pregunta del visitante y genera un draft
    profesional, conciso, en primera persona del agente.

    conversation_messages: lista de {sender, content} con el historial.
    """
    if not conversation_messages:
        return ''

    services_lines = '\n'.join(
        f'- {s["name"]} ({s.get("duration", "?")} min · ${s.get("price", "?")} MXN)'
        for s in tenant_context.get('services', [])
    ) or '(sin servicios cargados)'
    doctors_lines = '\n'.join(
        f'- {d["name"]} — {d.get("specialty") or "Medicina General"}'
        for d in tenant_context.get('doctors', [])
    ) or '(sin doctores cargados)'

    transcript = '\n'.join(
        f'{m.get("sender", "?").upper()}: {m.get("content", "")}'
        for m in conversation_messages[-15:]
    )

    prompt = (
        f'Eres un asistente que ayuda a un agente de SOPORTE de la clínica '
        f'"{tenant_context.get("name", "")}" a redactar respuestas profesionales.\n\n'
        f'INFORMACIÓN DE LA CLÍNICA:\n'
        f'Servicios:\n{services_lines}\n\n'
        f'Doctores:\n{doctors_lines}\n\n'
        f'CONVERSACIÓN ACTUAL (VISITOR=cliente, AGENT=agente):\n{transcript}\n\n'
        f'REGLAS:\n'
        f'- Escribís en primera persona como agente humano (no IA, no asistente).\n'
        f'- Respondés directamente al último mensaje del VISITOR.\n'
        f'- Si pregunta cómo agendar, explicale los pasos concretos: ir al sitio web, '
        f'sección "Agendar cita", elegir doctor, servicio, fecha y horario disponible.\n'
        f'- Tono profesional, cálido, en español. 2-4 oraciones.\n'
        f'- NO uses comillas, no expliques, no agregues firma.\n\n'
        f'Tu respuesta sugerida:'
    )

    try:
        resp = httpx.post(
            f'{settings.OLLAMA_BASE_URL}/api/generate',
            json={'model': settings.OLLAMA_MODEL_TEXT, 'prompt': prompt, 'stream': False},
            timeout=settings.OLLAMA_TIMEOUT * 3,
        )
        resp.raise_for_status()
        text = (resp.json().get('response') or '').strip()
        # Limpiar comillas a veces el modelo agrega
        text = text.strip().strip('"').strip("'")
        return text or ''
    except Exception as exc:
        logger.warning('Ollama suggest_agent_reply failed: %s', exc)
        return ''


def chat_reply(
    user_message: str,
    history: list[dict],
    tenant_context: dict,
) -> str:
    """
    Genera una respuesta conversacional para el chat público de la clínica.

    history: lista de {"role": "user|assistant", "content": "..."}
    tenant_context: {
        "name": str,
        "services": [{"name", "duration", "price"}],
        "doctors":  [{"name", "specialty"}],
    }

    Devuelve string con la respuesta. Si Ollama falla, retorna un fallback
    genérico (no levantamos excepción para no romper el chat).
    """
    services_lines = '\n'.join(
        f'- {s["name"]} ({s.get("duration", "?")} min · ${s.get("price", "?")} MXN)'
        for s in tenant_context.get('services', [])
    ) or '(sin servicios cargados)'
    doctors_lines = '\n'.join(
        f'- {d["name"]} — {d.get("specialty") or "Medicina General"}'
        for d in tenant_context.get('doctors', [])
    ) or '(sin doctores cargados)'

    history_text = ''
    for m in history[-8:]:  # últimos 8 turnos
        role = 'Usuario' if m.get('role') == 'user' else 'Asistente'
        history_text += f'{role}: {m.get("content", "")}\n'

    prompt = (
        f'Eres el asistente virtual de la clínica "{tenant_context.get("name", "")}".\n'
        f'Sé amable, conciso y profesional. Respondé en español.\n\n'
        f'INFORMACIÓN DE LA CLÍNICA:\n'
        f'Servicios disponibles:\n{services_lines}\n\n'
        f'Doctores:\n{doctors_lines}\n\n'
        f'REGLAS:\n'
        f'- Si el paciente pregunta cómo agendar, decile que en la sección "Agendar cita" '
        f'puede elegir doctor, servicio y horario.\n'
        f'- No inventes precios ni horarios que no estén arriba.\n'
        f'- Si no podés ayudar con la consulta o el paciente pide hablar con alguien, '
        f'decile que apriete el botón "Hablar con un agente humano".\n'
        f'- Mantené las respuestas cortas (2-4 oraciones máx).\n\n'
        f'CONVERSACIÓN PREVIA:\n{history_text}\n'
        f'Usuario: {user_message}\n'
        f'Asistente:'
    )

    try:
        resp = httpx.post(
            f'{settings.OLLAMA_BASE_URL}/api/generate',
            json={'model': settings.OLLAMA_MODEL_TEXT, 'prompt': prompt, 'stream': False},
            timeout=settings.OLLAMA_TIMEOUT * 3,  # las respuestas chat son más largas
        )
        resp.raise_for_status()
        text = (resp.json().get('response') or '').strip()
        return text or 'Disculpá, no pude generar una respuesta. ¿Querés hablar con un agente humano?'
    except Exception as exc:
        logger.warning('Ollama chat_reply failed: %s', exc)
        return (
            'Tuve un problema técnico procesando tu consulta. '
            'Probá apretar "Hablar con un agente humano" y alguien te atiende en seguida.'
        )
