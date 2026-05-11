import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from dotenv import load_dotenv
from corsheaders.defaults import default_headers

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-in-production')
SECRET_KEY_LOCAL = os.getenv('SECRET_KEY_LOCAL', SECRET_KEY)

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,.miapp.com').split(',')

# ── Applications ─────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    # Jazzmin must be before django.contrib.admin
    'jazzmin',

    # Daphne must be listed BEFORE django.contrib.staticfiles for ASGI dev server.
    'daphne',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'channels',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_prometheus',
    'dynamic_preferences',
    'dynamic_preferences.users.apps.UserPreferencesConfig',
    'colorfield',
    'mozilla_django_oidc',

    # django-users-auth (lib propia — email como USERNAME_FIELD)
    'users',

    # Celery Beat
    'django_celery_beat',

    # Local
    'apps.tenants',
    'apps.accounts',
    'apps.catalog',
    'apps.bookings',
    'apps.notifications',
    'apps.reports',
    'apps.ai',
    'apps.meetings',
    'apps.platform',
    'apps.support',
]

AUTH_USER_MODEL = 'users.User'

# ── Channels (WebSockets) ─────────────────────────────────────────────────────

ASGI_APPLICATION = 'core.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/2')],
        },
    },
}

# ── Middleware ────────────────────────────────────────────────────────────────

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.tenants.middleware.TenantMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dynamic_preferences.processors.global_preferences',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://martin:1234@localhost:5432/agendamiento-saas')
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Cache (Redis) ─────────────────────────────────────────────────────────────

REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 300,
    }
}

# ── Auth ──────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'mozilla_django_oidc.auth.OIDCAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Config para CustomJWTAuthentication de django-users-auth
# SECRET_KEY aquí es la clave usada para firmar/verificar tokens JWT locales (HS256)
DJANGO_USERS_AUTH_TOKEN = True
USERS_AUTH = {
    'SECRET_KEY': os.getenv('SECRET_KEY_LOCAL', SECRET_KEY),
    'TOKEN_ALGORITHM': 'HS256',
    'PUBLIC_KEY': None,
    'OIDC_OP_BASE_URL': os.getenv('OIDC_OP_BASE_URL', ''),
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Simple JWT ────────────────────────────────────────────────────────────────

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_ACCESS_LIFETIME_DAYS', 30))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_LIFETIME_DAYS', 30))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY_LOCAL,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ── Django REST Framework ─────────────────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.managers.CustomJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'shared.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('THROTTLE_ANON', '100/hour'),
        'user': os.getenv('THROTTLE_USER', '1000/hour'),
        'booking_create': os.getenv('THROTTLE_BOOKING_CREATE', '5/hour'),
        'slots': os.getenv('THROTTLE_SLOTS', '60/hour'),
    },
}

# ── CORS ──────────────────────────────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'True') == 'True'
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if not CORS_ALLOW_ALL_ORIGINS else []
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000,http://localhost:3001,http://localhost:3002').split(',')

CORS_ALLOW_HEADERS = list(default_headers) + ['x-tenant-slug']

# ── OIDC (Keycloak) ───────────────────────────────────────────────────────────

OIDC_RP_CLIENT_ID = os.getenv('OIDC_RP_CLIENT_ID', '')
OIDC_RP_CLIENT_SECRET = os.getenv('OIDC_RP_CLIENT_SECRET', '')
OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv('OIDC_OP_AUTHORIZATION_ENDPOINT', '')
OIDC_OP_TOKEN_ENDPOINT = os.getenv('OIDC_OP_TOKEN_ENDPOINT', '')
OIDC_OP_USER_ENDPOINT = os.getenv('OIDC_OP_USER_ENDPOINT', '')
OIDC_OP_JWKS_ENDPOINT = os.getenv('OIDC_OP_JWKS_ENDPOINT', '')
OIDC_RP_SIGN_ALGO = os.getenv('OIDC_RP_SIGN_ALGO', 'RS256')

# ── Internationalization ──────────────────────────────────────────────────────

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Static & Media ────────────────────────────────────────────────────────────

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Tenancy ───────────────────────────────────────────────────────────────────

PLATFORM_DOMAIN = os.getenv('PLATFORM_DOMAIN', 'miapp.com')
TENANT_EXEMPT_HOSTS = {
    PLATFORM_DOMAIN,
    f'www.{PLATFORM_DOMAIN}',
    f'api.{PLATFORM_DOMAIN}',
    'localhost',
    '127.0.0.1',
}

# ── Email ─────────────────────────────────────────────────────────────────────

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@miapp.com')

# Plantilla del URL del panel admin por tenant — usada por el email de activación.
# {slug} se reemplaza con el slug del tenant. En prod cambiar a 'https://admin.{slug}.miapp.com'.
ADMIN_BASE_URL_TEMPLATE = os.getenv('ADMIN_BASE_URL_TEMPLATE', 'http://admin.{slug}.miapp.com:3002')

# Base URL para servir media (fotos de perfil, etc.) desde WebSockets, donde
# no tenemos un objeto request del cual derivarla.
MEDIA_BASE_URL = os.getenv('MEDIA_BASE_URL', 'http://localhost:8000')

# ── Celery ─────────────────────────────────────────────────────────────────────

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'send-appointment-reminders-daily': {
        'task': 'apps.notifications.tasks.task_send_reminders',
        'schedule': 60 * 60 * 24,  # every 24 h (use crontab in prod if needed)
    },
}

# ── Kafka ─────────────────────────────────────────────────────────────────────

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_ENABLED = os.getenv('KAFKA_ENABLED', 'False') == 'True'

# ── Jazzmin (Django admin theming) ────────────────────────────────────────────

JAZZMIN_SETTINGS = {
    'site_title': 'Agendamiento SaaS — Plataforma',
    'site_header': 'Plataforma Admin',
    'site_brand': 'NexoSoft',
    'welcome_sign': 'Bienvenido al panel de plataforma',
    'copyright': 'NexoSoft',
    'search_model': ['tenants.Tenant', 'users.User'],
    'show_ui_builder': False,
}

# ── Dynamic Preferences ───────────────────────────────────────────────────────

DYNAMIC_PREFERENCES = {
    'MANAGER_ATTRIBUTE': 'pref',
    'REGISTRY_MODULE': 'preferences',
    'ENABLE_CACHE': True,
    'CACHE_NAME': 'default',
    'CACHE_KEY_PREFIX': 'dynpref',
}

# ── Security (prod hardening) ─────────────────────────────────────────────────

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ── AI / Ollama ───────────────────────────────────────────────────────────────

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL_TEXT = os.getenv('OLLAMA_MODEL_TEXT', 'gemma2:9b')
OLLAMA_MODEL_EMBED = os.getenv('OLLAMA_MODEL_EMBED', 'nomic-embed-text:latest')
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', 10))

# ── PayPal Subscriptions ──────────────────────────────────────────────────────
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')  # 'sandbox' o 'live'
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', '')
PAYPAL_SECRET = os.getenv('PAYPAL_SECRET', '')
PAYPAL_WEBHOOK_ID = os.getenv('PAYPAL_WEBHOOK_ID', '')
PAYPAL_API_BASE = (
    'https://api-m.sandbox.paypal.com'
    if PAYPAL_MODE == 'sandbox'
    else 'https://api-m.paypal.com'
)
PAYPAL_RETURN_URL = os.getenv('PAYPAL_RETURN_URL', 'http://localhost:3002/ajustes')
PAYPAL_CANCEL_URL = os.getenv('PAYPAL_CANCEL_URL', 'http://localhost:3002/ajustes')
