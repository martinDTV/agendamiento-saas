from rest_framework.permissions import BasePermission

from apps.accounts.models import Membership, MembershipRole


class IsSupportAgent(BasePermission):
    """
    Permite acceso a usuarios con rol SUPPORT, ADMIN u OWNER del tenant actual.
    """
    message = 'Necesitás rol de soporte o administrador para acceder al panel.'

    def has_permission(self, request, view):
        user = request.user
        tenant = getattr(request, 'tenant', None)
        if not user or not user.is_authenticated or not tenant:
            return False
        return Membership._all.filter(
            tenant=tenant,
            user=user,
            is_active=True,
            role__in=[MembershipRole.OWNER, MembershipRole.ADMIN, MembershipRole.SUPPORT],
        ).exists()
