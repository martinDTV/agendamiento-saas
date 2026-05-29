from datetime import datetime, timedelta, date as date_type
from typing import Optional

from apps.catalog.models import Doctor, Service, Schedule
from .models import Appointment, AppointmentStatus


def get_available_slots(
    doctor: Doctor,
    service: Service,
    target_date: date_type,
) -> list[dict]:
    """
    Returns available time slots for the given doctor/service/date.

    Slots are generated from the doctor's schedule for that weekday,
    split into intervals equal to service.duration, then filtered
    to exclude already-booked slots (pending or confirmed).
    """
    weekday = target_date.weekday()

    try:
        schedule = Schedule.objects.for_tenant(doctor.tenant).get(
            doctor=doctor,
            weekday=weekday,
            is_active=True,
        )
    except Schedule.DoesNotExist:
        return []

    duration = timedelta(minutes=service.duration)
    slots = []
    current = datetime.combine(target_date, schedule.start_time)
    end = datetime.combine(target_date, schedule.end_time)

    while current + duration <= end:
        slots.append({
            'start': current.time().strftime('%H:%M'),
            'end': (current + duration).time().strftime('%H:%M'),
        })
        current += duration

    # Fetch booked slots for this doctor/date
    booked = list(
        Appointment.objects.for_tenant(doctor.tenant).filter(
            doctor=doctor,
            date=target_date,
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED],
        ).values_list('start_time', 'end_time')
    )

    def overlaps(slot: dict) -> bool:
        from datetime import time as time_type
        s_start = datetime.strptime(slot['start'], '%H:%M').time()
        s_end = datetime.strptime(slot['end'], '%H:%M').time()
        for b_start, b_end in booked:
            if s_start < b_end and s_end > b_start:
                return True
        return False

    return [s for s in slots if not overlaps(s)]


def get_next_available_slot(
    doctor: Doctor,
    days_ahead: int = 14,
) -> Optional[dict]:
    """
    Devuelve el primer slot libre del doctor en los próximos `days_ahead` días.

    Útil para mostrar "Próxima disponibilidad" en la card del doctor sin que
    el paciente tenga que abrir el wizard de reserva.

    Usa el primer service activo del doctor para calcular la duración del
    slot (todos sus servicios suelen tener duración similar). Si el doctor
    no tiene servicios o no tiene schedule, devuelve None.

    Returns:
      {'date': 'YYYY-MM-DD', 'start': 'HH:MM'} o None
    """
    # Tomamos el primer servicio activo del doctor para usar su duración.
    # Esto es una aproximación — para la card es suficiente.
    service = (
        Service.objects.for_tenant(doctor.tenant)
        .filter(doctors=doctor, is_active=True)
        .first()
    )
    if not service:
        return None

    today = date_type.today()
    for offset in range(days_ahead):
        target = today + timedelta(days=offset)
        slots = get_available_slots(doctor, service, target)
        if slots:
            return {'date': target.isoformat(), 'start': slots[0]['start']}
    return None
