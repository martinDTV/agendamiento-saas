import pytest
from django.http import Http404
from django.test import RequestFactory

from apps.tenants.middleware import TenantMiddleware
from apps.tenants.models import Tenant


def make_get_response(request):
    from django.http import HttpResponse
    return HttpResponse('ok')


def make_middleware(get_response=None):
    return TenantMiddleware(get_response or make_get_response)


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        slug='drlopez',
        name='Dr. López',
        type='solo',
        is_active=True,
    )


@pytest.mark.django_db
class TestTenantMiddlewareResolution:
    def test_resolves_public_subdomain(self, factory, tenant):
        request = factory.get('/', HTTP_HOST='drlopez.miapp.com')
        mw = make_middleware()
        mw._resolve_tenant(request)
        assert request.tenant == tenant

    def test_resolves_admin_subdomain(self, factory, tenant):
        request = factory.get('/', HTTP_HOST='admin.drlopez.miapp.com')
        mw = make_middleware()
        mw._resolve_tenant(request)
        assert request.tenant == tenant

    def test_platform_host_sets_none(self, factory):
        request = factory.get('/', HTTP_HOST='miapp.com')
        mw = make_middleware()
        mw._resolve_tenant(request)
        assert request.tenant is None

    def test_api_host_sets_none(self, factory):
        request = factory.get('/', HTTP_HOST='api.miapp.com')
        mw = make_middleware()
        mw._resolve_tenant(request)
        assert request.tenant is None

    def test_localhost_sets_none(self, factory):
        request = factory.get('/', HTTP_HOST='localhost')
        mw = make_middleware()
        mw._resolve_tenant(request)
        assert request.tenant is None

    def test_unknown_slug_raises_404(self, factory, db):
        request = factory.get('/', HTTP_HOST='unknown.miapp.com')
        mw = make_middleware()
        with pytest.raises(Http404):
            mw._resolve_tenant(request)

    def test_inactive_tenant_raises_404(self, factory, db):
        Tenant.objects.create(slug='inactive', name='Inactive', is_active=False)
        request = factory.get('/', HTTP_HOST='inactive.miapp.com')
        mw = make_middleware()
        with pytest.raises(Http404):
            mw._resolve_tenant(request)

    def test_custom_domain_resolution(self, factory, db):
        tenant = Tenant.objects.create(
            slug='drsmith',
            name='Dr. Smith',
            custom_domain='drsmith.com',
            is_active=True,
        )
        request = factory.get('/', HTTP_HOST='drsmith.com')
        mw = make_middleware()
        mw._resolve_tenant(request)
        assert request.tenant == tenant

    def test_host_with_port_is_handled(self, factory, tenant):
        request = factory.get('/', SERVER_NAME='drlopez.miapp.com', SERVER_PORT='8000')
        request.META['HTTP_HOST'] = 'drlopez.miapp.com:8000'
        mw = make_middleware()
        mw._resolve_tenant(request)
        assert request.tenant == tenant
