"""
Límites de equipo para tenants con plan demo.

Un tenant demo (plan='demo' o settings['demo']=True, creados por
DemoTenantMiddleware) puede tener como máximo:
  - 2 doctores
  - 1 administrador (además del owner)
  - 1 staff
  - 0 usuarios de soporte

Se valida en cada punto de alta de miembros: invitaciones
(InvitationCreateSerializer), alta directa de doctores/admins
(DoctorViewSet.create) y cambios de rol (MembershipViewSet).
"""

from apps.accounts.models import Membership, MembershipRole

DEMO_ROLE_LIMITS = {
    MembershipRole.DOCTOR: 2,
    MembershipRole.ADMIN: 1,
    MembershipRole.STAFF: 1,
    MembershipRole.SUPPORT: 0,
}

_ROLE_LABELS = {
    MembershipRole.DOCTOR: 'doctores',
    MembershipRole.ADMIN: 'administrador',
    MembershipRole.STAFF: 'usuario staff',
}


def is_demo_tenant(tenant) -> bool:
    if tenant is None:
        return False
    return tenant.plan == 'demo' or bool((tenant.settings or {}).get('demo'))


def demo_role_error(tenant, role, *, extra_pending: int = 0, exclude_membership_id=None):
    """
    Devuelve un mensaje de error si agregar un miembro más con `role` excede
    los límites del plan demo; None si está permitido (o el tenant no es demo).

    `extra_pending` suma cupos ya comprometidos (p. ej. invitaciones sin
    aceptar). `exclude_membership_id` excluye una membresía del conteo (para
    cambios de rol sobre una membresía existente).
    """
    if not is_demo_tenant(tenant):
        return None

    limit = DEMO_ROLE_LIMITS.get(role)
    if limit is None:  # rol sin límite (p. ej. owner — nunca llega aquí)
        return None
    if limit == 0:
        return 'El plan demo no permite crear usuarios de soporte.'

    qs = Membership._all.filter(tenant=tenant, role=role, is_active=True)
    if exclude_membership_id is not None:
        qs = qs.exclude(id=exclude_membership_id)
    current = qs.count() + extra_pending

    if current >= limit:
        label = _ROLE_LABELS.get(role, role)
        return f'El plan demo permite máximo {limit} {label}.'
    return None
