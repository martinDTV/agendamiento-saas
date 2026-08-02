# Bitácora — 2026-08-02: SMTP real, fix de invitaciones y plan de WhatsApp

Sesión de trabajo sobre el stack demo (`/opt/agendamiento-demo`), continuación de la sesión de la madrugada del mismo día.

## Qué se hizo

### 1. Correo real (SMTP Gmail) en el demo
- `core/demo_settings.py` ahora usa el backend SMTP cuando existe `EMAIL_HOST_USER` en el entorno; sin credenciales cae al backend de consola (los correos solo se imprimen en los logs).
- Remitente global del demo: `vazquezmartin1240@gmail.com` (vía `DEFAULT_FROM_EMAIL`). Aplica a todos los tenants porque se configura por variables de entorno del backend, no por tenant.
- Las invitaciones de equipo (`apps/accounts/views.py`, `from_email=None`) y los correos de activación de tenants desde el panel platform usan ese remitente.
- Verificado end-to-end con el tenant `prueba-demo`: la invitación llegó (a spam la primera vez — normal para una cuenta Gmail que apenas empieza a mandar HTML con links; marcar "No es spam" lo corrige rápido).

### 2. Fix: links de invitación apuntaban al dominio de desarrollo
- Síntoma: el botón "Aceptar invitación" mandaba a `http://admin.prueba-demo.miapp.com:3002/...`.
- Causa: `ADMIN_BASE_URL_TEMPLATE` nunca se definió para el entorno demo y se usaba el default de desarrollo.
- Fix en `core/demo_settings.py`:
  - `ADMIN_BASE_URL_TEMPLATE = https://admin-{slug}.demo-agendamiento.nexosoftdev.com` (formato que rutea Caddy).
  - `MEDIA_BASE_URL` también se corrigió (apuntaba a `localhost:8000`; afectaba fotos de perfil en el chat).
- Los tokens de invitaciones ya enviadas siguen válidos; solo cambia la URL del correo.

### 3. Commit y push del trabajo acumulado
- Commit `f3b38c1` — 17 archivos: SMTP, `ADMIN_BASE_URL_TEMPLATE`/`MEDIA_BASE_URL`, servicio `platform` en compose + `Dockerfile.platform`, volumen `demo_media` para uploads, `apps/tenants/demo_limits.py` (límites por tenant en demo), ajustes al flujo de invitaciones y panel platform, seed mínimo opcional, fixes de frontend (página equipo, layout admin, landing marketing).
- Push a GitHub desbloqueado configurando una **deploy key SSH con write access** en `martinDTV/agendamiento-saas`; el remoto `origin` quedó en `git@github.com:martinDTV/agendamiento-saas.git`. Los pushes futuros desde el droplet ya no necesitan token.

## Decisiones / plan de negocio (bot de WhatsApp)

Objetivo: vender a 5–6 doctores a **$1,000 MXN/mes** con dos canales: página web + bot de WhatsApp para agendar, con las conversaciones visibles en el panel.

Números validados:

| Concepto | Estimado mensual |
|---|---|
| Ingreso (5–6 doctores × $1,000) | $5,000–6,000 MXN |
| Droplet | $450–900 MXN |
| WhatsApp Cloud API — sesiones iniciadas por el paciente | $0 |
| Plantillas de utilidad (recordatorios/confirmaciones, ~500–800/mes) | $150–250 MXN |
| Email + dominio | ~$30 MXN |
| **Margen bruto** | **~75–85%** |

Diseño técnico acordado:
- Reutilizar el módulo de soporte existente (conversaciones + Django Channels) agregando un campo `source: 'web' | 'whatsapp'`.
- El bot es un webhook de Meta Cloud API que llama los mismos endpoints de booking que la web (flujo guiado: doctor → servicio → horario → confirmar).
- Cada interacción queda como conversación + cita en la BD del tenant, visible en el panel admin.
- A futuro: componente de credenciales de correo por tenant, con el Gmail como remitente de respaldo. Para producción real, dominio propio + servicio transaccional (Resend/SES/Mailgun) con SPF/DKIM.

## Pendiente / siguiente paso

- **Empezar el bot de WhatsApp** (canal 2). No queda nada sin commitear.
