"""
Validadores de formato para identificadores mexicanos.

Cada validator es un `RegexValidator` con su patrón exacto. Se usan tanto en
los campos del modelo (vía `validators=[...]`) como en los serializers (que
los disparan automáticamente al hacer `is_valid()`).

Los inputs vacíos NO se validan (los campos son `blank=True`). La normalización
(uppercase, quitar espacios/guiones) se hace en el serializer ANTES de validar.
"""
from django.core.validators import RegexValidator


# ── CURP ─────────────────────────────────────────────────────────────────────
# Estructura oficial (RENAPO, 18 chars):
#   1-4:  Iniciales del apellido paterno, materno y primer nombre [A-Z]{4}
#   5-10: Fecha de nacimiento YYMMDD
#   11:   Sexo: H (hombre) o M (mujer)
#   12-13: Entidad federativa de nacimiento (clave de 2 letras)
#   14-16: Primeras consonantes internas de los apellidos y nombre
#   17:   Homoclave (0-9 o A-Z, asignada por RENAPO para distinguir homónimos)
#   18:   Dígito verificador (0-9, antes podía ser A para homoclaves viejas)
#
# No validamos checksum del dígito verificador acá — eso requiere lookup contra
# RENAPO y se sale del scope. El regex sí garantiza estructura.
CURP_REGEX = r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d$'
curp_validator = RegexValidator(
    regex=CURP_REGEX,
    message=(
        'CURP inválido. Debe tener 18 caracteres con el formato oficial '
        '(ej. PEPJ800101HDFRRR01).'
    ),
    code='invalid_curp',
)


# ── RFC persona física ───────────────────────────────────────────────────────
# Estructura SAT, 13 chars:
#   1-4:  Iniciales del primer apellido + segundo + nombre [A-Z&Ñ]{4}
#   5-10: Fecha de nacimiento YYMMDD
#   11-13: Homoclave (3 chars alfanuméricos, 0-9 o A-Z)
#
# Nota: para personas morales el RFC tiene 12 chars, pero pacientes = persona
# física → siempre 13. Si en el futuro hay clientes facturando como persona
# moral usaríamos otro field.
RFC_REGEX = r'^[A-ZÑ&]{4}\d{6}[0-9A-Z]{3}$'
rfc_validator = RegexValidator(
    regex=RFC_REGEX,
    message=(
        'RFC inválido. Debe tener 13 caracteres para persona física '
        '(ej. PEPJ800101AB1).'
    ),
    code='invalid_rfc',
)


# ── Teléfono MX ──────────────────────────────────────────────────────────────
# Aceptamos solo 10 dígitos (sin formato visual). El serializer normaliza el
# input quitando espacios, guiones, paréntesis y el prefijo '+52' o '52'
# antes de validar, así que el usuario puede escribir "+52 55 1234 5678" o
# "(55) 1234-5678" — todos quedan como "5512345678".
PHONE_MX_REGEX = r'^\d{10}$'
phone_mx_validator = RegexValidator(
    regex=PHONE_MX_REGEX,
    message='Teléfono inválido. Debe tener 10 dígitos (lada incluida).',
    code='invalid_phone_mx',
)


# ── Código postal MX ─────────────────────────────────────────────────────────
ZIP_MX_REGEX = r'^\d{5}$'
zip_mx_validator = RegexValidator(
    regex=ZIP_MX_REGEX,
    message='Código postal inválido. Debe tener 5 dígitos.',
    code='invalid_zip_mx',
)


# ── Helpers de normalización ─────────────────────────────────────────────────

def normalize_curp(value: str) -> str:
    """Quita espacios y pasa a uppercase. Vacío → vacío."""
    if not value:
        return ''
    return value.strip().upper().replace(' ', '')


def normalize_rfc(value: str) -> str:
    """Idéntico a CURP — quitar espacios y uppercase."""
    if not value:
        return ''
    return value.strip().upper().replace(' ', '')


def normalize_phone_mx(value: str) -> str:
    """
    Convierte cualquier representación a 10 dígitos crudos.

    Ej:
       '+52 55 1234 5678'  → '5512345678'
       '(55) 1234-5678'    → '5512345678'
       '52 5512345678'     → '5512345678'

    Si después de limpiar el número tiene 12 o 13 dígitos y empieza con '52'
    o '521' (lada de país), lo quitamos. El validator de 10 dígitos hace lo
    demás.
    """
    if not value:
        return ''
    digits = ''.join(ch for ch in value if ch.isdigit())
    # Lada México '52' o '521' (móviles legacy)
    if len(digits) == 12 and digits.startswith('52'):
        digits = digits[2:]
    elif len(digits) == 13 and digits.startswith('521'):
        digits = digits[3:]
    return digits


def normalize_zip_mx(value: str) -> str:
    """Solo dígitos, sin espacios."""
    if not value:
        return ''
    return ''.join(ch for ch in value if ch.isdigit())
