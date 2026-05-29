"""
Tests del flujo de modificar/cancelar citas desde la app del paciente.

Cubre:
  - GET detalle: solo el paciente owner ve la cita.
  - PATCH (reagendar): valida slot disponible, no permite fecha pasada,
    requiere 24h de anticipación.
  - DELETE (cancelar): cambia status a 'cancelled', no borra; requiere 24h.
"""
from datetime import date, datetime, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.bookings.models import Appointment, AppointmentStatus
from apps.catalog.models import Branch, Doctor, Schedule, Service
from apps.patients.models import Patient
from apps.tenants.models import Tenant


User = get_user_model()


@pytest.fixture
def setup(db):
    tenant = Tenant.objects.create(slug='mod-c', name='Clínica Mod')
    Branch._all.create(tenant=tenant, name='Sede')
    dr_user = User.objects.create_user(
        username='dr@m.com', email='dr@m.com', password='x',
        first_name='Doc', last_name='Tor',
    )
    doctor = Doctor._all.create(
        tenant=tenant, user=dr_user, specialty='G', appointment_duration=30,
    )
    service = Service._all.create(
        tenant=tenant, name='Consulta', duration=30, price=500,
    )
    service.doctors.add(doctor)
    # Schedule de 9am a 6pm todos los días para que haya slots
    for wd in range(7):
        Schedule._all.create(
            tenant=tenant, doctor=doctor, weekday=wd,
            start_time=time(9, 0), end_time=time(18, 0), is_active=True,
        )
    return {'tenant': tenant, 'doctor': doctor, 'service': service}


def _make_patient(email='p@p.com'):
    user = User.objects.create_user(
        username=email, email=email, password='x',
        first_name='Pac', is_active=True,
    )
    return Patient.objects.create(user=user), user


def _auth_client(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


def _future_appointment(setup, patient, days_ahead=5):
    """Crea una cita en el futuro con un horario que existe en el schedule."""
    return Appointment._all.create(
        tenant=setup['tenant'],
        doctor=setup['doctor'],
        service=setup['service'],
        patient=patient,
        patient_name='Test', patient_email='p@p.com', patient_phone='5511111111',
        date=date.today() + timedelta(days=days_ahead),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status=AppointmentStatus.CONFIRMED,
    )


# ── GET detalle ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAppointmentDetail:
    def _url(self, appt_id):
        return f'/rest/v1/patients/me/appointments/{appt_id}/'

    def test_owner_can_get_detail(self, setup):
        patient, user = _make_patient()
        appt = _future_appointment(setup, patient)
        client = _auth_client(user)
        res = client.get(self._url(appt.id))
        assert res.status_code == 200
        assert res.data['id'] == str(appt.id)

    def test_other_patient_cannot_see(self, setup):
        patient_a, _ = _make_patient('a@p.com')
        appt = _future_appointment(setup, patient_a)
        _, user_b = _make_patient('b@p.com')
        client = _auth_client(user_b)
        res = client.get(self._url(appt.id))
        assert res.status_code == 404  # no expone que existe

    def test_unauthenticated_rejected(self, setup):
        patient, _ = _make_patient()
        appt = _future_appointment(setup, patient)
        client = APIClient()
        res = client.get(self._url(appt.id))
        assert res.status_code == 401


# ── DELETE (cancelar) ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCancelAppointment:
    def _url(self, appt_id):
        return f'/rest/v1/patients/me/appointments/{appt_id}/'

    def test_cancel_changes_status(self, setup):
        patient, user = _make_patient()
        appt = _future_appointment(setup, patient)
        client = _auth_client(user)
        res = client.delete(self._url(appt.id))
        assert res.status_code == 200
        appt.refresh_from_db()
        assert appt.status == AppointmentStatus.CANCELLED

    def test_cancel_does_not_delete(self, setup):
        patient, user = _make_patient()
        appt = _future_appointment(setup, patient)
        client = _auth_client(user)
        client.delete(self._url(appt.id))
        # La cita sigue existiendo (no se borró físicamente)
        assert Appointment._all.filter(pk=appt.id).exists()

    def test_already_cancelled_returns_400(self, setup):
        patient, user = _make_patient()
        appt = _future_appointment(setup, patient)
        appt.status = AppointmentStatus.CANCELLED
        appt.save()
        client = _auth_client(user)
        res = client.delete(self._url(appt.id))
        assert res.status_code == 400

    def test_within_24h_rejected(self, setup):
        patient, user = _make_patient()
        # Cita HOY en 1 hora — debería rechazar
        soon = (datetime.now() + timedelta(hours=1))
        appt = Appointment._all.create(
            tenant=setup['tenant'],
            doctor=setup['doctor'],
            service=setup['service'],
            patient=patient,
            patient_name='T', patient_email='p@p.com', patient_phone='5511111111',
            date=soon.date(),
            start_time=soon.time().replace(second=0, microsecond=0),
            end_time=(soon + timedelta(minutes=30)).time().replace(second=0, microsecond=0),
            status=AppointmentStatus.CONFIRMED,
        )
        client = _auth_client(user)
        res = client.delete(self._url(appt.id))
        assert res.status_code == 400


# ── PATCH (reagendar) ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRescheduleAppointment:
    def _url(self, appt_id):
        return f'/rest/v1/patients/me/appointments/{appt_id}/'

    def test_reschedule_to_valid_slot(self, setup):
        patient, user = _make_patient()
        appt = _future_appointment(setup, patient)
        new_date = (date.today() + timedelta(days=7)).isoformat()
        client = _auth_client(user)
        res = client.patch(self._url(appt.id), {
            'date': new_date, 'start_time': '11:00',
        }, format='json')
        assert res.status_code == 200, res.data
        appt.refresh_from_db()
        assert appt.start_time == time(11, 0)
        assert appt.end_time == time(11, 30)  # +30 min de duración

    def test_reschedule_to_past_date_rejected(self, setup):
        patient, user = _make_patient()
        appt = _future_appointment(setup, patient)
        client = _auth_client(user)
        res = client.patch(self._url(appt.id), {
            'date': (date.today() - timedelta(days=1)).isoformat(),
            'start_time': '11:00',
        }, format='json')
        assert res.status_code == 400

    def test_reschedule_missing_fields_rejected(self, setup):
        patient, user = _make_patient()
        appt = _future_appointment(setup, patient)
        client = _auth_client(user)
        res = client.patch(self._url(appt.id), {}, format='json')
        assert res.status_code == 400

    def test_reschedule_to_unavailable_slot_rejected(self, setup):
        """Si el slot está fuera del schedule del doctor → 400."""
        patient, user = _make_patient()
        appt = _future_appointment(setup, patient)
        client = _auth_client(user)
        # 03:00 AM no está en el horario 9-18
        res = client.patch(self._url(appt.id), {
            'date': (date.today() + timedelta(days=7)).isoformat(),
            'start_time': '03:00',
        }, format='json')
        assert res.status_code == 400
