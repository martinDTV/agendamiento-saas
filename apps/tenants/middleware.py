import re

from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.utils import timezone

from apps.tenants.exceptions import TenantNotFoundError, TenantInactiveError


class TenantMiddleware:
    """
    Resolves the current tenant from the Host header and attaches it to the request.

    Subdomains resolved:
      {slug}.miapp.com           → public site
      admin.{slug}.miapp.com     → admin panel
      {custom_domain}            → custom domain lookup

    Sets request.tenant = Tenant instance, or None for platform-level hosts.
    Returns 404 for unknown slugs or inactive tenants.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_hosts = getattr(settings, 'TENANT_EXEMPT_HOSTS', set())
        self.platform_domain = getattr(settings, 'PLATFORM_DOMAIN', 'miapp.com')

    def __call__(self, request):
        self._resolve_tenant(request)
        return self.get_response(request)

    def _resolve_tenant(self, request):
        # Use META directly to avoid ALLOWED_HOSTS validation —
        # custom domains are resolved by the app, not by Django's host check.
        host = request.META.get('HTTP_HOST', '').split(':')[0].lower()

        if host in self.exempt_hosts:
            request.tenant = None
        else:
            slug = self._extract_slug(host)

            if slug is None:
                tenant = self._resolve_by_custom_domain(host)
                request.tenant = tenant
            else:
                try:
                    request.tenant = self._get_active_tenant(slug)
                except TenantNotFoundError:
                    raise Http404(f"No existe un tenant con slug '{slug}'.")
                except TenantInactiveError:
                    raise Http404(f"El tenant '{slug}' no está activo.")

        # X-Tenant-Slug fallback: used by Nuxt SSR and programmatic API calls
        # where the subdomain is not available (localhost, testserver, internal IPs).
        if request.tenant is None:
            header_slug = request.META.get('HTTP_X_TENANT_SLUG', '').strip().lower()
            if header_slug:
                try:
                    request.tenant = self._get_active_tenant(header_slug)
                except (TenantNotFoundError, TenantInactiveError):
                    request.tenant = None

    def _extract_slug(self, host):
        """
        Returns the tenant slug from a subdomain host, or None if it cannot be extracted.

        admin.drlopez.miapp.com → 'drlopez'
        drlopez.miapp.com       → 'drlopez'
        unrelated.example.com   → None
        """
        if not host.endswith(self.platform_domain):
            return None

        prefix = host[: len(host) - len(self.platform_domain)].rstrip('.')
        if not prefix:
            return None

        parts = prefix.split('.')
        if len(parts) >= 2 and parts[0] == 'admin':
            return parts[1]
        return parts[0]

    def _resolve_by_custom_domain(self, host):
        from apps.tenants.models import Tenant

        try:
            return Tenant.objects.get(custom_domain=host, is_active=True)
        except Tenant.DoesNotExist:
            return None
        except Exception:
            # Protect against DB being unavailable during startup
            return None

    @staticmethod
    def _get_active_tenant(slug):
        from apps.tenants.models import Tenant

        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            raise TenantNotFoundError(slug)

        if not tenant.is_active:
            raise TenantInactiveError(slug)

        return tenant


# Slugs that must never become a demo clinic (system / reserved subdomains).
DEMO_RESERVED_SLUGS = {
    'admin', 'www', 'api', 'app', 'demo', 'demo-agendamiento',
    'static', 'media', 'assets', 'mail', 'smtp', 'ftp', 'ns', 'ns1', 'ns2',
}

_SLUG_RE = re.compile(r'^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$')


def is_valid_demo_slug(slug):
    return slug not in DEMO_RESERVED_SLUGS and bool(_SLUG_RE.match(slug))


def _demo_quota_key(ip):
    # One counter per IP per UTC day.
    day = timezone.now().strftime('%Y%m%d')
    return f'demo:create:{day}:{ip}'


def get_or_create_demo_tenant(slug, client_ip=None):
    """
    Return the demo tenant for `slug`, creating + seeding it on first request.

    Used both by DemoTenantMiddleware (subdomain hit) and by the resolve
    endpoint (Nuxt SSR passes the slug in the URL while the Host is the apex).
    Returns None if DEMO_MODE is off or the slug is reserved/invalid.

    If `client_ip` is given, enforces a per-IP daily creation limit
    (DEMO_MAX_PER_IP_PER_DAY). Accessing an already-existing demo never counts;
    only creating a new one does. Raises DemoLimitReachedError when exceeded.
    """
    from django.core.cache import cache

    from apps.tenants.demo_seed import seed_tenant
    from apps.tenants.exceptions import DemoLimitReachedError
    from apps.tenants.models import Tenant

    if not getattr(settings, 'DEMO_MODE', False) or not is_valid_demo_slug(slug):
        return None

    # Existing demo? Return it without touching the quota.
    existing = Tenant.objects.filter(slug=slug, is_active=True).first()
    if existing is not None:
        return existing

    # New tenant: enforce the per-IP daily quota before creating.
    limit = getattr(settings, 'DEMO_MAX_PER_IP_PER_DAY', 2)
    quota_key = None
    if client_ip and limit:
        quota_key = _demo_quota_key(client_ip)
        used = cache.get(quota_key, 0)
        if used >= limit:
            raise DemoLimitReachedError(client_ip)

    ttl_days = getattr(settings, 'DEMO_TENANT_TTL_DAYS', 7)
    name = slug.replace('-', ' ').title()
    expires_at = timezone.now() + timezone.timedelta(days=ttl_days)

    with transaction.atomic():
        tenant, created = Tenant.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'type': 'clinic',
                'plan': 'demo',
                'is_active': True,
                'settings': {
                    'demo': True,
                    'demo_expires_at': expires_at.isoformat(),
                    'timezone': 'America/Mexico_City',
                    'locale': 'es-MX',
                },
            },
        )
        if created:
            seed_tenant(tenant)

    # Count this creation against the IP's daily quota (expires after ~24h).
    if created and quota_key:
        try:
            cache.set(quota_key, cache.get(quota_key, 0) + 1, timeout=86400)
        except Exception:
            pass

    return tenant


class DemoTenantMiddleware(TenantMiddleware):
    """
    Demo variant of TenantMiddleware.

    When DEMO_MODE is on and the host resolves to a slug that does not yet exist,
    the tenant is created on the fly, seeded with sample data, and given an
    expiry timestamp (purge_demo_tenants removes it later). This powers
    `<clinic>.demo-agendamiento.nexosoftdev.com` self-service demos.

    Only active under core.demo_settings (DEMO_MODE=True). With DEMO_MODE off it
    behaves exactly like the base middleware, so it is safe everywhere.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.demo_mode = getattr(settings, 'DEMO_MODE', False)
        self.demo_ttl_days = getattr(settings, 'DEMO_TENANT_TTL_DAYS', 7)

    def _get_active_tenant(self, slug):
        try:
            return super()._get_active_tenant(slug)
        except TenantNotFoundError:
            tenant = get_or_create_demo_tenant(slug)
            if tenant is None:
                raise
            return tenant
