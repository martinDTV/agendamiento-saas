from rest_framework import viewsets

from apps.accounts.permissions import IsTenantAdminOrOwner, IsTenantMember


class TenantScopedViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet that automatically scopes querysets to request.tenant
    and injects tenant on creation.

    Subclasses must set `queryset` to the model class (used only for router
    basename inference). Override `get_queryset` only when extra filtering
    is needed beyond the tenant scope.
    """

    def get_queryset(self):
        return self.queryset.model.objects.for_tenant(self.request.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)
