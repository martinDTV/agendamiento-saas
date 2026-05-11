from apps.accounts.permissions import IsTenantAdminOrOwner, IsTenantMember
from shared.viewsets import TenantScopedViewSet

from .models import Room, Meeting
from .serializers import RoomSerializer, MeetingSerializer


class RoomViewSet(TenantScopedViewSet):
    queryset = Room._all.all()
    serializer_class = RoomSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsTenantMember()]
        return [IsTenantAdminOrOwner()]

    def get_queryset(self):
        qs = Room.objects.for_tenant(self.request.tenant).select_related('branch')
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        active = self.request.query_params.get('active')
        if active == 'true':
            qs = qs.filter(is_active=True)
        return qs


class MeetingViewSet(TenantScopedViewSet):
    queryset = Meeting._all.all()
    serializer_class = MeetingSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsTenantMember()]
        return [IsTenantAdminOrOwner()]

    def get_queryset(self):
        from django.db.models import Q
        from apps.accounts.models import Membership, MembershipRole

        qs = (
            Meeting.objects.for_tenant(self.request.tenant)
            .select_related('organizer', 'room__branch')
            .prefetch_related('participants')
        )

        # Doctors only see meetings they organize or participate in
        membership = Membership.objects.for_tenant(self.request.tenant).filter(
            user=self.request.user, is_active=True,
        ).first()
        if membership and membership.role == MembershipRole.DOCTOR:
            qs = qs.filter(Q(organizer=self.request.user) | Q(participants=self.request.user)).distinct()

        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)
        return qs
