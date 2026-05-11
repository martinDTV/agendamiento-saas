from rest_framework.permissions import BasePermission


class IsPlatformAdmin(BasePermission):
    """Solo superusuarios de la plataforma pueden acceder."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)
