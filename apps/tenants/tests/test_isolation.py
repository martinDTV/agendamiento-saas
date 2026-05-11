import pytest
from shared.models import TenantScopeRequired, TenantScopedModel
from apps.tenants.models import Tenant
from django.db import models


# ── Concrete model used only for testing ──────────────────────────────────────

class SampleRecord(TenantScopedModel):
    """Minimal concrete subclass used to verify TenantScopedModel behaviour."""
    note = models.CharField(max_length=100, default='test')

    class Meta(TenantScopedModel.Meta):
        app_label = 'tenants'


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tenant_a(db):
    return Tenant.objects.create(slug='tenant-a', name='Tenant A', is_active=True)


@pytest.fixture
def tenant_b(db):
    return Tenant.objects.create(slug='tenant-b', name='Tenant B', is_active=True)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestTenantManager:
    def test_direct_all_raises(self):
        """Model.objects.all() must raise without tenant scope."""
        with pytest.raises(TenantScopeRequired):
            SampleRecord.objects.all()

    def test_direct_filter_raises(self):
        """Model.objects.filter() must raise without tenant scope."""
        with pytest.raises(TenantScopeRequired):
            SampleRecord.objects.filter(note='x')

    def test_for_tenant_returns_queryset(self, tenant_a):
        """for_tenant() returns a QuerySet without raising."""
        qs = SampleRecord.objects.for_tenant(tenant_a)
        assert qs is not None

    def test_for_tenant_accepts_uuid(self, tenant_a):
        """for_tenant() accepts a raw UUID in addition to a Tenant instance."""
        qs = SampleRecord.objects.for_tenant(tenant_a.pk)
        assert qs is not None


@pytest.mark.django_db
class TestTenantIsolation:
    def test_tenant_a_cannot_see_tenant_b_records(self, tenant_a, tenant_b):
        """Records created for tenant B must be invisible when querying for tenant A."""
        SampleRecord._all.create(tenant=tenant_b, note='secret')

        qs = SampleRecord.objects.for_tenant(tenant_a)
        assert qs.count() == 0

    def test_tenant_sees_only_own_records(self, tenant_a, tenant_b):
        """Tenant A sees only its own records when records exist for both tenants."""
        SampleRecord._all.create(tenant=tenant_a, note='mine')
        SampleRecord._all.create(tenant=tenant_b, note='not-mine')

        qs = SampleRecord.objects.for_tenant(tenant_a)
        assert qs.count() == 1
        assert qs.first().note == 'mine'

    def test_unscoped_all_objects_bypass(self, tenant_a, tenant_b):
        """_all manager should return records from all tenants (for internal use)."""
        SampleRecord._all.create(tenant=tenant_a, note='a')
        SampleRecord._all.create(tenant=tenant_b, note='b')

        assert SampleRecord._all.count() == 2
