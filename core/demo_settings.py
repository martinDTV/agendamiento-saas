"""
Settings for the ISOLATED demo environment.

Run with:  DJANGO_SETTINGS_MODULE=core.demo_settings

Everything inherits from core.settings; this module only changes what must be
different so the demo can never touch production data or send real messages:

  - DATABASES['default'] points at DEMO_DATABASE_URL (a SEPARATE Postgres).
  - PLATFORM_DOMAIN is the demo wildcard domain.
  - DEMO_MODE enables on-the-fly tenant creation via DemoTenantMiddleware.
  - Email is forced to the console backend (no real correos in demo).
  - Twilio / WhatsApp sending is disabled.
"""

import os

import dj_database_url

from core.settings import *  # noqa: F401,F403
from core.settings import MIDDLEWARE as _BASE_MIDDLEWARE

# ── Isolation: separate database ───────────────────────────────────────────────
# Falls back to a local "agendamiento-saas-demo" db. In production this is set to
# the demo Postgres container's URL and is NEVER the production DATABASE_URL.
DEMO_DATABASE_URL = os.getenv(
    'DEMO_DATABASE_URL',
    'postgresql://martin:1234@localhost:5432/agendamiento-saas-demo',
)
DATABASES = {
    'default': dj_database_url.parse(DEMO_DATABASE_URL, conn_max_age=600),
}

# ── Demo tenancy ────────────────────────────────────────────────────────────────
DEMO_MODE = True
DEMO_TENANT_TTL_DAYS = int(os.getenv('DEMO_TENANT_TTL_DAYS', '7'))

# DEMO_PLATFORM_DOMAIN takes precedence so a local .env PLATFORM_DOMAIN (used by
# production settings) cannot accidentally point the demo at the prod domain.
PLATFORM_DOMAIN = os.getenv('DEMO_PLATFORM_DOMAIN', 'demo-agendamiento.nexosoftdev.com')
TENANT_EXEMPT_HOSTS = {
    PLATFORM_DOMAIN,
    f'www.{PLATFORM_DOMAIN}',
    f'api.{PLATFORM_DOMAIN}',
    'localhost',
    '127.0.0.1',
}

ALLOWED_HOSTS = os.getenv(
    'ALLOWED_HOSTS',
    f'localhost,127.0.0.1,{PLATFORM_DOMAIN},.{PLATFORM_DOMAIN}',
).split(',')

# Swap the tenant middleware for the auto-creating demo variant.
MIDDLEWARE = [
    'apps.tenants.middleware.DemoTenantMiddleware'
    if m == 'apps.tenants.middleware.TenantMiddleware' else m
    for m in _BASE_MIDDLEWARE
]

# ── No real outbound messages in demo ───────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'demo@demo-agendamiento.nexosoftdev.com'

# Disable WhatsApp / SMS sending if the project reads these flags.
WHATSAPP_ENABLED = False
TWILIO_ENABLED = False
