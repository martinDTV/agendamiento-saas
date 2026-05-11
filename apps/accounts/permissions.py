from rest_framework.permissions import BasePermission

from apps.accounts.models import Membership, MembershipRole


def _get_membership(request):
    """Returns the active Membership for the current user in request.tenant, or None."""
    tenant = getattr(request, 'tenant', None)
    if not tenant or not request.user or not request.user.is_authenticated:
        return None
    try:
        return Membership.objects.for_tenant(tenant).get(user=request.user, is_active=True)
    except Membership.DoesNotExist:
        return None


class IsTenantMember(BasePermission):
    """Any active member of the current tenant."""

    def has_permission(self, request, view):
        return _get_membership(request) is not None


class IsTenantOwner(BasePermission):
    """Only the tenant owner."""

    def has_permission(self, request, view):
        m = _get_membership(request)
        return m is not None and m.role == MembershipRole.OWNER


class IsTenantAdminOrOwner(BasePermission):
    """Owner or admin of the current tenant."""

    def has_permission(self, request, view):
        m = _get_membership(request)
        return m is not None and m.has_role_at_least(MembershipRole.ADMIN)


class IsTenantDoctorOrAbove(BasePermission):
    """Doctor, admin, or owner."""

    def has_permission(self, request, view):
        m = _get_membership(request)
        return m is not None and m.has_role_at_least(MembershipRole.DOCTOR)
