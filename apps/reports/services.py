"""
Aggregation logic for the appointment reports.

Shared by the JSON endpoint (AppointmentReportView) and the Excel export so the
numbers always match. Everything is tenant-scoped by the caller passing a
pre-filtered queryset.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce, TruncDay, TruncMonth

from apps.bookings.models import Appointment, AppointmentStatus

# Statuses that represent realized (billable) appointments for revenue.
REVENUE_STATUSES = [AppointmentStatus.COMPLETED, AppointmentStatus.CONFIRMED]

STATUS_LABELS = {
    AppointmentStatus.PENDING: 'Pendiente',
    AppointmentStatus.CONFIRMED: 'Confirmada',
    AppointmentStatus.CANCELLED: 'Cancelada',
    AppointmentStatus.COMPLETED: 'Completada',
}

WEEKDAY_LABELS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def parse_range(from_raw, to_raw):
    """Parse YYYY-MM-DD strings, falling back to the last 30 days."""
    today = date.today()
    try:
        from_date = date.fromisoformat(from_raw) if from_raw else today - timedelta(days=30)
        to_date = date.fromisoformat(to_raw) if to_raw else today
    except (ValueError, TypeError):
        from_date = today - timedelta(days=30)
        to_date = today
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    return from_date, to_date


def base_queryset(tenant, from_date, to_date):
    return (
        Appointment.objects.for_tenant(tenant)
        .filter(date__gte=from_date, date__lte=to_date)
    )


def build_report(tenant, from_date, to_date):
    """Return the full stats payload for the given tenant + date range."""
    qs = base_queryset(tenant, from_date, to_date)
    total = qs.count()

    # ── By status ─────────────────────────────────────────────────────────
    status_counts = {
        row['status']: row['total']
        for row in qs.values('status').annotate(total=Count('id'))
    }
    by_status = {
        'pending': status_counts.get(AppointmentStatus.PENDING, 0),
        'confirmed': status_counts.get(AppointmentStatus.CONFIRMED, 0),
        'cancelled': status_counts.get(AppointmentStatus.CANCELLED, 0),
        'completed': status_counts.get(AppointmentStatus.COMPLETED, 0),
    }

    # ── No-show / cancellation rate ───────────────────────────────────────
    cancelled = by_status['cancelled']
    completed = by_status['completed']
    decided = cancelled + completed
    cancellation_rate = round((cancelled / decided) * 100, 1) if decided else 0.0
    completion_rate = round((completed / decided) * 100, 1) if decided else 0.0

    # ── By doctor (with revenue) ──────────────────────────────────────────
    money = DecimalField(max_digits=12, decimal_places=2)
    by_doctor = [
        {
            'id': str(row['doctor__id']),
            'name': f"{row['doctor__user__first_name']} {row['doctor__user__last_name']}".strip(),
            'total': row['total'],
            'revenue': float(row['revenue'] or 0),
        }
        for row in qs.values('doctor__id', 'doctor__user__first_name', 'doctor__user__last_name')
        .annotate(
            total=Count('id'),
            revenue=Coalesce(
                Sum('service__price', filter=_revenue_filter(), output_field=money),
                Decimal('0'),
                output_field=money,
            ),
        )
        .order_by('-total')[:10]
    ]

    # ── By service (with revenue) ─────────────────────────────────────────
    by_service = [
        {
            'id': str(row['service__id']),
            'name': row['service__name'],
            'total': row['total'],
            'revenue': float(row['revenue'] or 0),
        }
        for row in qs.values('service__id', 'service__name')
        .annotate(
            total=Count('id'),
            revenue=Coalesce(
                Sum('service__price', filter=_revenue_filter(), output_field=money),
                Decimal('0'),
                output_field=money,
            ),
        )
        .order_by('-total')[:10]
    ]

    # ── Total estimated revenue ───────────────────────────────────────────
    revenue_total = float(
        qs.filter(status__in=REVENUE_STATUSES).aggregate(
            v=Coalesce(Sum('service__price', output_field=money), Decimal('0'), output_field=money)
        )['v']
    )

    # ── Time trend ────────────────────────────────────────────────────────
    span_days = (to_date - from_date).days
    if span_days > 92:
        trend_rows = (
            qs.annotate(bucket=TruncMonth('date')).values('bucket')
            .annotate(total=Count('id')).order_by('bucket')
        )
        trend_granularity = 'month'
    else:
        trend_rows = (
            qs.annotate(bucket=TruncDay('date')).values('bucket')
            .annotate(total=Count('id')).order_by('bucket')
        )
        trend_granularity = 'day'
    trend = [
        {'date': row['bucket'].isoformat() if row['bucket'] else None, 'total': row['total']}
        for row in trend_rows
    ]

    # ── Occupancy by weekday × hour ───────────────────────────────────────
    # Returns a list of {weekday: 0-6, hour: 0-23, total} for a heatmap.
    occupancy = []
    for row in qs.values('date', 'start_time').annotate(total=Count('id')):
        wd = row['date'].weekday()
        hr = row['start_time'].hour
        occupancy.append((wd, hr, row['total']))
    # Collapse into a dict then flatten
    heat = {}
    for wd, hr, t in occupancy:
        heat[(wd, hr)] = heat.get((wd, hr), 0) + t
    occupancy_cells = [
        {'weekday': wd, 'hour': hr, 'total': t}
        for (wd, hr), t in sorted(heat.items())
    ]

    return {
        'from_date': str(from_date),
        'to_date': str(to_date),
        'total': total,
        'by_status': by_status,
        'cancellation_rate': cancellation_rate,
        'completion_rate': completion_rate,
        'revenue_total': revenue_total,
        'by_doctor': by_doctor,
        'by_service': by_service,
        'trend': trend,
        'trend_granularity': trend_granularity,
        'occupancy': occupancy_cells,
    }


def _revenue_filter():
    from django.db.models import Q
    return Q(status__in=REVENUE_STATUSES)
