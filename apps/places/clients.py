"""
Clientes HTTP para autocomplete de direcciones por código postal mexicano.

Tres providers en cascada (orden de preferencia):

1. **Copomex** (primario) — Envuelve la base oficial de SEPOMEX. Es la ÚNICA
   fuente confiable de TODAS las colonias de un CP mexicano. Requiere token
   gratuito de https://copomex.com (200 requests/día en plan gratis).
   Doc: https://api.copomex.com

2. **Zippopotam.us** (fallback) — API pública sin key, pero solo devuelve UNA
   colonia y a veces con nombre inventado. Útil cuando copomex falla.

3. **Google Places API New** (último recurso) — usa GOOGLE_PLACES_API_KEY.
   Solo devuelve estado/ciudad de áreas con cobertura urbana — no siempre da
   colonia. Cuesta dinero por llamada.

Returns en los tres: dict con la misma forma:
    {
      "postal_code": "06600",
      "state":      "Ciudad de México",
      "city":       "Ciudad de México",
      "neighborhoods": ["Juárez", "Roma Norte", ...],  # lista de colonias
      "country":    "México",
      "lat":        19.385,                  # opcional
      "lng":        -99.165,                 # opcional
      "source":     "copomex" | "zippopotam" | "google"
    }

Si NINGÚN provider responde, lanzamos `PostalCodeNotFound`.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


COPOMEX_URL = 'https://api.copomex.com/query/info_cp/{cp}'
ZIPPOPOTAM_URL = 'https://api.zippopotam.us/mx/{cp}'
GOOGLE_TEXT_SEARCH_URL = 'https://places.googleapis.com/v1/places:searchText'

HTTP_TIMEOUT_SEC = 5.0


class PostalCodeNotFound(Exception):
    """Ningún provider devolvió datos para el CP."""


class PostalCodeProviderError(Exception):
    """Error técnico del provider (red, 5xx, etc.). Distinto de 'no existe'."""


@dataclass
class PostalCodeInfo:
    postal_code: str
    state: str
    city: str
    neighborhoods: list[str] = field(default_factory=list)
    country: str = 'México'
    lat: Optional[float] = None
    lng: Optional[float] = None
    source: str = ''

    def to_dict(self) -> dict:
        return {
            'postal_code': self.postal_code,
            'state': self.state,
            'city': self.city,
            'neighborhoods': self.neighborhoods,
            'country': self.country,
            'lat': self.lat,
            'lng': self.lng,
            'source': self.source,
        }


# ── Provider 1: Copomex (datos oficiales SEPOMEX) ────────────────────────────

def fetch_from_copomex(cp: str) -> Optional[PostalCodeInfo]:
    """
    Devuelve info del CP usando copomex.com (envuelve la base SEPOMEX oficial).

    Esta es la ÚNICA fuente confiable de TODAS las colonias mexicanas. Si está
    configurado COPOMEX_TOKEN, es el provider primario.

    Returns None si:
      - No hay token configurado
      - El CP no se encuentra
    Raises PostalCodeProviderError en fallos técnicos.
    """
    token = getattr(settings, 'COPOMEX_TOKEN', '')
    if not token:
        logger.info('COPOMEX_TOKEN no configurado — saltando provider')
        return None

    url = COPOMEX_URL.format(cp=cp)
    try:
        resp = requests.get(url, params={'token': token}, timeout=HTTP_TIMEOUT_SEC)
    except requests.RequestException as e:
        raise PostalCodeProviderError(f'copomex network: {e}')

    if resp.status_code == 404:
        return None
    if resp.status_code >= 500:
        raise PostalCodeProviderError(f'copomex {resp.status_code}')
    if resp.status_code != 200:
        # Token inválido suele venir como 4xx con mensaje.
        try:
            body = resp.json()
        except ValueError:
            body = {}
        msg = body.get('error_message') or body.get('error') or resp.text[:200]
        logger.warning('copomex %s: %s', resp.status_code, msg)
        return None

    try:
        data = resp.json()
    except ValueError:
        raise PostalCodeProviderError('copomex returned non-JSON')

    # Copomex devuelve una LISTA de entradas (una por colonia/asentamiento)
    # o un objeto con `error: true` si el CP no existe.
    if isinstance(data, dict) and data.get('error'):
        return None
    if not isinstance(data, list) or not data:
        return None

    # Tomamos estado/ciudad de la primera entrada (son iguales en todas),
    # y juntamos los nombres de los asentamientos como colonias.
    first_response = data[0].get('response') or {}
    if not first_response:
        return None

    state = first_response.get('estado', '')
    city = first_response.get('ciudad') or first_response.get('municipio', '')

    neighborhoods: list[str] = []
    for entry in data:
        r = entry.get('response') or {}
        name = (r.get('asentamiento') or '').strip()
        if name and name not in neighborhoods:
            neighborhoods.append(name)

    return PostalCodeInfo(
        postal_code=cp,
        state=state,
        city=city,
        neighborhoods=neighborhoods,
        country=first_response.get('pais', 'México'),
        source='copomex',
    )


# ── Provider 2: Zippopotam (fallback gratis) ─────────────────────────────────

def fetch_from_zippopotam(cp: str) -> Optional[PostalCodeInfo]:
    """
    Devuelve info del CP usando zippopotam.us.

    Limitaciones: solo da UNA colonia por CP y a veces con dato sucio
    (ej. el CP 79034 dice "Mision San Miguel" cuando en realidad es
    Ciudad Valles / Palo de Rosa). Por eso es fallback, no primario.
    """
    url = ZIPPOPOTAM_URL.format(cp=cp)
    try:
        resp = requests.get(url, timeout=HTTP_TIMEOUT_SEC)
    except requests.RequestException as e:
        raise PostalCodeProviderError(f'zippopotam network: {e}')

    if resp.status_code == 404:
        return None
    if resp.status_code >= 500:
        raise PostalCodeProviderError(f'zippopotam {resp.status_code}')
    if resp.status_code != 200:
        return None

    data = resp.json()
    places = data.get('places') or []
    if not places:
        return None

    first = places[0]
    neighborhoods = [p.get('place name', '').strip() for p in places if p.get('place name')]
    state = first.get('state', '')
    if state.lower() == 'distrito federal':
        state = 'Ciudad de México'

    # Zippopotam NO tiene un campo de ciudad/municipio real — su `place name`
    # corresponde más bien al asentamiento/colonia. Lo metemos en
    # `neighborhoods` y dejamos `city=''` para que el frontend NO ponga la
    # colonia como ciudad por accidente. (Bug que tuvimos en producción).
    return PostalCodeInfo(
        postal_code=cp,
        state=state,
        city='',  # zippopotam no sabe la ciudad real
        neighborhoods=neighborhoods,
        country='México',
        lat=_to_float(first.get('latitude')),
        lng=_to_float(first.get('longitude')),
        source='zippopotam',
    )


# ── Provider 3: Google Places API New ───────────────────────────────────────

def fetch_from_google(cp: str) -> Optional[PostalCodeInfo]:
    """
    Devuelve info del CP usando Google Places API New (textSearch).
    Limitaciones: no siempre da colonia, y cuesta dinero por llamada.
    """
    api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', '')
    if not api_key:
        return None

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'places.formattedAddress,places.addressComponents,places.location',
    }
    body = {
        'textQuery': f'código postal {cp} México',
        'languageCode': 'es',
        'regionCode': 'MX',
        'maxResultCount': 5,
    }

    try:
        resp = requests.post(
            GOOGLE_TEXT_SEARCH_URL, json=body, headers=headers,
            timeout=HTTP_TIMEOUT_SEC,
        )
    except requests.RequestException as e:
        raise PostalCodeProviderError(f'google network: {e}')

    if resp.status_code == 403:
        logger.error('Google Places 403: %s', resp.text[:200])
        raise PostalCodeProviderError('google 403')
    if resp.status_code >= 500:
        raise PostalCodeProviderError(f'google {resp.status_code}')
    if resp.status_code != 200:
        return None

    data = resp.json() or {}
    places = data.get('places') or []
    if not places:
        return None

    state = ''
    city = ''
    country = 'México'
    neighborhoods: list[str] = []
    lat = lng = None

    for place in places:
        loc = place.get('location') or {}
        if loc and lat is None:
            lat = _to_float(loc.get('latitude'))
            lng = _to_float(loc.get('longitude'))

        for comp in place.get('addressComponents', []):
            types = comp.get('types', [])
            text = comp.get('longText', '')
            if 'administrative_area_level_1' in types and not state:
                state = text
            elif 'locality' in types and not city:
                city = text
            elif 'sublocality' in types or 'sublocality_level_1' in types:
                if text and text not in neighborhoods:
                    neighborhoods.append(text)
            elif 'country' in types:
                country = text

    if not state and not neighborhoods:
        return None

    return PostalCodeInfo(
        postal_code=cp,
        state=state,
        city=city or (neighborhoods[0] if neighborhoods else ''),
        neighborhoods=neighborhoods,
        country=country,
        lat=lat,
        lng=lng,
        source='google',
    )


# ── Orquestador ──────────────────────────────────────────────────────────────

def lookup_postal_code(cp: str) -> PostalCodeInfo:
    """
    Resuelve un CP usando los providers en cascada.

    Estrategia: copomex > zippopotam > google. El primero que devuelva datos
    útiles, gana. Si todos fallan o ninguno encuentra el CP, lanza
    PostalCodeNotFound.

    NO cachea aquí — el cacheo lo hace la view con `cache.set`.
    """
    cp = cp.strip()
    if not (cp.isdigit() and len(cp) == 5):
        raise PostalCodeNotFound(f'CP inválido: {cp!r}')

    providers = [
        ('copomex', fetch_from_copomex),
        ('zippopotam', fetch_from_zippopotam),
        ('google', fetch_from_google),
    ]

    last_error: Optional[Exception] = None
    for name, fn in providers:
        try:
            result = fn(cp)
            if result:
                return result
        except PostalCodeProviderError as e:
            logger.warning('Provider %s falló para CP %s: %s', name, cp, e)
            last_error = e

    if last_error:
        raise PostalCodeProviderError(f'Todos los providers fallaron: {last_error}')

    raise PostalCodeNotFound(f'CP {cp} no encontrado en ningún provider')


def _to_float(v) -> Optional[float]:
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ── Geocoding (dirección libre → lat/lng) ────────────────────────────────────


@dataclass
class GeocodeResult:
    lat: float
    lng: float
    formatted_address: str
    source: str = 'google'


def geocode_address(address: str) -> Optional[GeocodeResult]:
    """
    Convierte una dirección libre en coordenadas usando Google Places API New.

    Usa el endpoint `searchText` (mismo que ya tenemos habilitado). Devuelve
    el PRIMER resultado — Google lo elige por relevancia.

    Returns None si:
      - No hay API key configurada
      - Google no encuentra la dirección
      - Cualquier error técnico (no propaga, devuelve None para no romper
        flujos donde la geocodificación es nice-to-have)
    """
    if not address or not address.strip():
        return None

    api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', '')
    if not api_key:
        logger.info('GOOGLE_PLACES_API_KEY no configurada — skip geocode')
        return None

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'places.formattedAddress,places.location',
    }
    body = {
        'textQuery': address.strip(),
        'languageCode': 'es',
        'regionCode': 'MX',
        'maxResultCount': 1,
    }

    try:
        resp = requests.post(
            GOOGLE_TEXT_SEARCH_URL, json=body, headers=headers,
            timeout=HTTP_TIMEOUT_SEC,
        )
    except requests.RequestException as e:
        logger.warning('geocode network error: %s', e)
        return None

    if resp.status_code != 200:
        logger.warning('geocode HTTP %s: %s', resp.status_code, resp.text[:200])
        return None

    data = resp.json() or {}
    places = data.get('places') or []
    if not places:
        return None

    first = places[0]
    loc = first.get('location') or {}
    lat = _to_float(loc.get('latitude'))
    lng = _to_float(loc.get('longitude'))
    if lat is None or lng is None:
        return None

    return GeocodeResult(
        lat=lat,
        lng=lng,
        formatted_address=first.get('formattedAddress', address),
        source='google',
    )
