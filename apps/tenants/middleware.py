from django.conf import settings
from django.http import Http404

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
