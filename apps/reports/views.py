from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsTenantMember

from .excel import build_workbook
from .services import build_report, parse_range


class AppointmentReportView(APIView):
    """
    GET /rest/v1/reports/appointments/

    Query params:
      from_date  YYYY-MM-DD  (default: 30 days ago)
      to_date    YYYY-MM-DD  (default: today)

    Returns stats: totals, by status/doctor/service, revenue, cancellation
    rate, time trend, and occupancy by weekday × hour.
    """
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        from_date, to_date = parse_range(
            request.query_params.get('from_date'),
            request.query_params.get('to_date'),
        )
        return Response(build_report(request.tenant, from_date, to_date))


class AppointmentReportExcelView(APIView):
    """
    GET /rest/v1/reports/appointments/export/

    Same params as the JSON report. Returns an .xlsx workbook with data sheets
    and native Excel charts.
    """
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        tenant = request.tenant
        from_date, to_date = parse_range(
            request.query_params.get('from_date'),
            request.query_params.get('to_date'),
        )
        report = build_report(tenant, from_date, to_date)
        workbook = build_workbook(report, getattr(tenant, 'name', 'Clínica'))

        filename = f'reporte-citas_{from_date}_{to_date}.xlsx'
        response = HttpResponse(
            workbook.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
