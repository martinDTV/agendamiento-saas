import uuid
from django.db import models


class TenantScopeRequired(RuntimeError):
    """Raised when a tenant-scoped model is queried without a tenant filter."""


class TenantQuerySet(models.QuerySet):
    pass


class TenantManager(models.Manager):
    """
    Default manager for TenantScopedModel subclasses.

    Accessing .objects directly raises TenantScopeRequired to prevent accidental
    cross-tenant data leaks. Always use .objects.for_tenant(tenant).
    """

    def get_queryset(self):
        raise TenantScopeRequired(
            f"{self.model.__name__}.objects.all() is forbidden. "
            "Use .objects.for_tenant(tenant) to scope queries."
        )

    def for_tenant(self, tenant):
        """Return a QuerySet scoped to the given Tenant instance or tenant_id."""
        tenant_id = tenant.pk if hasattr(tenant, 'pk') else tenant
        return TenantQuerySet(self.model, using=self._db).filter(tenant_id=tenant_id)


class UnscopedManager(models.Manager):
    """
    Internal manager used by Django for migrations, related lookups, and admin.
    Not intended for use in application code.
    """

    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)


class TenantScopedModel(models.Model):
    """
    Abstract base for all models that belong to a single tenant.

    Django internals (migrations, related managers) use `_all`, which returns
    the unfiltered QuerySet. Application code must use `objects.for_tenant(t)`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
    )

    # Django uses _all for internal operations (FK lookups, admin, migrations)
    _all = UnscopedManager()

    # Application code uses objects — raises without .for_tenant()
    objects = TenantManager()

    class Meta:
        abstract = True
        base_manager_name = '_all'
