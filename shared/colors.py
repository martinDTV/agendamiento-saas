"""
Color helpers for email templates and UI rendering server-side.

Las plantillas de email usan inline CSS y no pueden ejecutar JS, así que
calculamos colores derivados (gradiente, hover, etc.) en Python.
"""

import re
from typing import Iterable


_HEX_RE = re.compile(r'^#?([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$')


def _parse_hex(color: str) -> tuple[int, int, int] | None:
    """Devuelve (r, g, b) o None si el formato es inválido."""
    if not color:
        return None
    m = _HEX_RE.match(color.strip())
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _to_hex(rgb: Iterable[int]) -> str:
    r, g, b = (max(0, min(255, int(c))) for c in rgb)
    return f'#{r:02X}{g:02X}{b:02X}'


def darken(color: str, amount: float = 0.2, fallback: str = '#4A7C59') -> str:
    """
    Devuelve una versión más oscura del color hex (multiplica cada canal por
    `1 - amount`). amount=0 → mismo color, amount=1 → negro.
    """
    rgb = _parse_hex(color)
    if rgb is None:
        rgb = _parse_hex(fallback) or (74, 124, 89)
    factor = max(0.0, min(1.0, 1.0 - amount))
    return _to_hex(c * factor for c in rgb)


def normalize_hex(color: str | None, fallback: str = '#6FA776') -> str:
    """Garantiza un hex de 7 caracteres (#RRGGBB) o devuelve fallback."""
    rgb = _parse_hex(color or '')
    if rgb is None:
        rgb = _parse_hex(fallback) or (111, 167, 118)
    return _to_hex(rgb)
