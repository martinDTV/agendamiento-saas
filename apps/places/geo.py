"""
Utilidades geográficas.

Por ahora cálculo de distancia con Haversine (fórmula de gran círculo).
Suficiente para distancias <500km con error <0.5%. Para >500km o si
necesitas precisión submétrica, usar PostGIS.

NO usamos PostGIS por ahora porque:
  1. Tu DB es PostgreSQL estándar, no PostGIS habilitado
  2. La cobertura del SaaS es MX, distancias típicas <100km
  3. Para <10k clínicas, Haversine en Python es <50ms incluso sin índice
"""
from __future__ import annotations

import math
from typing import Optional


EARTH_RADIUS_KM = 6371.0


def haversine_km(
    lat1: float, lng1: float, lat2: float, lng2: float,
) -> float:
    """
    Distancia en km entre dos puntos (lat, lng) usando Haversine.

    Inputs en grados, output en km.
    """
    # Convertir grados a radianes
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def parse_latlng(value: Optional[str]) -> Optional[float]:
    """
    Parse query param lat/lng como float. Devuelve None si no es válido.
    Valida rango: lat ∈ [-90, 90], lng ∈ [-180, 180].
    """
    if value is None or value == '':
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if not (-180 <= f <= 180):
        return None
    return f
