from datetime import date, timedelta

from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsTenantMember
from apps.bookings.models import Appointment, AppointmentStatus


class AppointmentReportView(APIView):
    """
    GET /rest/v1/reports/appointments/

    Query params:
      from_date  YYYY-MM-DD  (default: 30 days ago)
      to_date    YYYY-MM-DD  (default: today)
    """
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        tenant = request.tenant
        today = date.today()

        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        try:
            from_date = date.fromisoformat(from_date) if from_date else today - timedelta(days=30)
            to_date = date.fromisoformat(to_date) if to_date else today
        except ValueError:
            from_date = today - timedelta(days=30)
            to_date = today

        qs = Appointment.objects.for_tenant(tenant).filter(date__gte=from_date, date__lte=to_date)

        by_status = {
            row['status']: row['total']
            for row in qs.values('status').annotate(total=Count('id'))
        }
        by_doctor = list(
            qs.values('doctor__user__first_name', 'doctor__user__last_name', 'doctor__id')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )
        by_service = list(
            qs.values('service__name', 'service__id')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )

        return Response({
            'from_date': str(from_date),
            'to_date': str(to_date),
            'total': qs.count(),
            'by_status': {
                'pending': by_status.get(AppointmentStatus.PENDING, 0),
                'confirmed': by_status.get(AppointmentStatus.CONFIRMED, 0),
                'cancelled': by_status.get(AppointmentStatus.CANCELLED, 0),
                'completed': by_status.get(AppointmentStatus.COMPLETED, 0),
            },
            'by_doctor': [
                {
                    'id': row['doctor__id'],
                    'name': f"{row['doctor__user__first_name']} {row['doctor__user__last_name']}".strip(),
                    'total': row['total'],
                }
                for row in by_doctor
            ],
            'by_service': [
                {'id': row['service__id'], 'name': row['service__name'], 'total': row['total']}
                for row in by_service
            ],
        })
