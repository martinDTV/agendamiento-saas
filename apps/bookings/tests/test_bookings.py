import pytest
from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Membership, MembershipRole
from apps.bookings.models import Appointment, AppointmentStatus
from apps.bookings.slots import get_available_slots
from apps.catalog.models import Doctor, Service, Schedule
from apps.tenants.models import Tenant

User = get_user_model()

MONDAY = date(2026, 5, 11)   # real Monday
TUESDAY = date(2026, 5, 12)


def make_tenant(slug):
    return Tenant.objects.create(slug=slug, name=slug, is_active=True)


def make_user(email):
    return User.objects.create_user(email=email, password='ValidPass123!')


def make_membership(tenant, user, role=MembershipRole.OWNER):
    return Membership._all.create(tenant=tenant, user=user, role=role)


def auth_client(user):
    client = APIClient()
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


@pytest.fixture
def setup():
    tenant = make_tenant('booking-clinic')
    owner = make_user('owner@booking.com')
    doc_user = make_user('doc@booking.com')
    make_membership(tenant, owner, MembershipRole.OWNER)
    make_membership(tenant, doc_user, MembershipRole.DOCTOR)

    doctor = Doctor._all.create(tenant=tenant, user=doc_user, appointment_duration=30)
    service = Service._all.create(
        tenant=tenant, name='Consulta', duration=30, price='350.00'
    )
    # Schedule: Monday 09:00–11:00
    schedule = Schedule._all.create(
        tenant=tenant, doctor=doctor,
        weekday=0, start_time=time(9, 0), end_time=time(11, 0),
    )
    return {
        'tenant': tenant, 'owner': owner,
        'doctor': doctor, 'service': service, 'schedule': schedule,
    }


# ── Slot generation ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSlotGeneration:
    def test_generates_correct_slots(self, setup):
        slots = get_available_slots(setup['doctor'], setup['service'], MONDAY)
        assert len(slots) == 4  # 09:00, 09:30, 10:00, 10:30
        assert slots[0] == {'start': '09:00', 'end': '09:30'}
        assert slots[-1] == {'start': '10:30', 'end': '11:00'}

    def test_no_slots_if_no_schedule(self, setup):
        slots = get_available_slots(setup['doctor'], setup['service'], TUESDAY)
        assert slots == []

    def test_booked_slot_removed(self, setup):
        Appointment._all.create(
            tenant=setup['tenant'],
            doctor=setup['doctor'],
            service=setup['service'],
            patient_name='Juan',
            patient_email='juan@t.com',
            date=MONDAY,
            start_time=time(9, 0),
            end_time=time(9, 30),
        )
        slots = get_available_slots(setup['doctor'], setup['service'], MONDAY)
        assert len(slots) == 3
        assert all(s['start'] != '09:00' for s in slots)

    def test_cancelled_slot_is_available(self, setup):
        Appointment._all.create(
            tenant=setup['tenant'],
            doctor=setup['doctor'],
            service=setup['service'],
            patient_name='Juan',
            patient_email='juan@t.com',
            date=MONDAY,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status=AppointmentStatus.CANCELLED,
        )
        slots = get_available_slots(setup['doctor'], setup['service'], MONDAY)
        assert len(slots) == 4  # cancelled doesn't block


# ── Public API ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPublicSlots:
    URL = '/rest/v1/public/slots/'

    def test_returns_slots_with_header(self, setup):
        client = APIClient()
        res = client.get(
            self.URL,
            {
                'doctor': str(setup['doctor'].id),
                'service': str(setup['service'].id),
                'date': str(MONDAY),
            },
            HTTP_X_TENANT_SLUG=setup['tenant'].slug,
        )
        assert res.status_code == 200
        assert len(res.data['slots']) == 4

    def test_missing_params_returns_400(self, setup):
        client = APIClient()
        res = client.get(
            self.URL,
            HTTP_X_TENANT_SLUG=setup['tenant'].slug,
        )
        assert res.status_code == 400


@pytest.mark.django_db
class TestPublicAppointmentCreate:
    URL = '/rest/v1/public/appointments/'

    def test_creates_appointment(self, setup):
        client = APIClient()
        res = client.post(
            self.URL,
            {
                'doctor': str(setup['doctor'].id),
                'service': str(setup['service'].id),
                'patient_name': 'María García',
                'patient_email': 'maria@t.com',
                'patient_phone': '5551234567',
                'date': str(MONDAY),
                'start_time': '09:00:00',
            },
            format='json',
            HTTP_X_TENANT_SLUG=setup['tenant'].slug,
        )
        assert res.status_code == 201
        assert Appointment.objects.for_tenant(setup['tenant']).count() == 1

    def test_duplicate_slot_returns_400(self, setup):
        client = APIClient()
        payload = {
            'doctor': str(setup['doctor'].id),
            'service': str(setup['service'].id),
            'patient_name': 'Ana',
            'patient_email': 'ana@t.com',
            'date': str(MONDAY),
            'start_time': '10:00:00',
        }
        client.post(self.URL, payload, format='json', HTTP_X_TENANT_SLUG=setup['tenant'].slug)
        res = client.post(self.URL, payload, format='json', HTTP_X_TENANT_SLUG=setup['tenant'].slug)
        assert res.status_code == 400

    def test_public_doctor_list(self, setup):
        client = APIClient()
        res = client.get(
            '/rest/v1/public/catalog/doctors/',
            HTTP_X_TENANT_SLUG=setup['tenant'].slug,
        )
        assert res.status_code == 200
        assert res.data['count'] == 1


# ── Admin appointments ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAdminAppointments:
    URL = '/rest/v1/bookings/appointments/'

    def _book(self, setup):
        return Appointment._all.create(
            tenant=setup['tenant'],
            doctor=setup['doctor'],
            service=setup['service'],
            patient_name='Test',
            patient_email='test@t.com',
            date=MONDAY,
            start_time=time(9, 0),
            end_time=time(9, 30),
        )

    def test_owner_can_list_appointments(self, setup):
        self._book(setup)
        client = auth_client(setup['owner'])
        res = client.get(
            self.URL,
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 200
        assert res.data['count'] == 1

    def test_owner_can_update_status(self, setup):
        appt = self._book(setup)
        client = auth_client(setup['owner'])
        res = client.patch(
            f'{self.URL}{appt.id}/',
            {'status': AppointmentStatus.CONFIRMED},
            format='json',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 200
        appt.refresh_from_db()
        assert appt.status == AppointmentStatus.CONFIRMED
