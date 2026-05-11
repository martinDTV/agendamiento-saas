import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Membership, MembershipRole
from apps.catalog.models import Branch, Doctor, Service, Schedule
from apps.tenants.models import Tenant

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────────────────────────

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
    tenant = make_tenant('clinic-a')
    owner = make_user('owner@clinic-a.com')
    staff = make_user('staff@clinic-a.com')
    make_membership(tenant, owner, MembershipRole.OWNER)
    make_membership(tenant, staff, MembershipRole.STAFF)

    other_tenant = make_tenant('clinic-b')
    other_owner = make_user('owner@clinic-b.com')
    make_membership(other_tenant, other_owner, MembershipRole.OWNER)

    return {
        'tenant': tenant,
        'owner': owner,
        'staff': staff,
        'other_tenant': other_tenant,
        'other_owner': other_owner,
    }


# ── Branch tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBranch:
    URL = '/rest/v1/catalog/branches/'

    def test_owner_can_create_branch(self, setup):
        client = auth_client(setup['owner'])
        client.tenant = setup['tenant']
        res = client.post(
            self.URL,
            {'name': 'Sucursal Norte', 'address': 'Calle 1', 'phone': '5551234567'},
            format='json',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 201
        assert Branch.objects.for_tenant(setup['tenant']).count() == 1

    def test_staff_cannot_create_branch(self, setup):
        # First create one branch as owner so the list is not empty
        Branch._all.create(tenant=setup['tenant'], name='Main')
        client = auth_client(setup['staff'])
        res = client.post(
            self.URL,
            {'name': 'Nueva', 'address': '', 'phone': ''},
            format='json',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 403

    def test_branch_isolated_between_tenants(self, setup):
        Branch._all.create(tenant=setup['tenant'], name='A-branch')
        Branch._all.create(tenant=setup['other_tenant'], name='B-branch')

        assert Branch.objects.for_tenant(setup['tenant']).count() == 1
        assert Branch.objects.for_tenant(setup['other_tenant']).count() == 1

    def test_owner_can_list_branches(self, setup):
        Branch._all.create(tenant=setup['tenant'], name='Branch 1')
        Branch._all.create(tenant=setup['tenant'], name='Branch 2')
        client = auth_client(setup['owner'])
        res = client.get(
            self.URL,
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 200
        assert res.data['count'] == 2


# ── Doctor tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDoctor:
    URL = '/rest/v1/catalog/doctors/'

    def test_create_doctor_for_tenant_user(self, setup):
        client = auth_client(setup['owner'])
        res = client.post(
            self.URL,
            {
                'user': setup['staff'].pk,
                'specialty': 'Medicina general',
                'appointment_duration': 30,
            },
            format='json',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 201
        assert Doctor.objects.for_tenant(setup['tenant']).count() == 1

    def test_duplicate_doctor_same_tenant_fails(self, setup):
        Doctor._all.create(tenant=setup['tenant'], user=setup['staff'])
        client = auth_client(setup['owner'])
        res = client.post(
            self.URL,
            {'user': setup['staff'].pk, 'specialty': 'Otra', 'appointment_duration': 30},
            format='json',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 400

    def test_same_user_can_be_doctor_in_two_tenants(self, setup):
        shared_user = make_user('shared@doc.com')
        make_membership(setup['tenant'], shared_user, MembershipRole.DOCTOR)
        make_membership(setup['other_tenant'], shared_user, MembershipRole.DOCTOR)

        Doctor._all.create(tenant=setup['tenant'], user=shared_user)
        Doctor._all.create(tenant=setup['other_tenant'], user=shared_user)

        assert Doctor.objects.for_tenant(setup['tenant']).count() == 1
        assert Doctor.objects.for_tenant(setup['other_tenant']).count() == 1


# ── Service tests ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestService:
    URL = '/rest/v1/catalog/services/'

    def test_create_service(self, setup):
        client = auth_client(setup['owner'])
        res = client.post(
            self.URL,
            {'name': 'Consulta general', 'duration': 30, 'price': '350.00', 'color': '#3B82F6'},
            format='json',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 201

    def test_service_isolated_between_tenants(self, setup):
        Service._all.create(tenant=setup['tenant'], name='S1', duration=30, price='100.00')
        Service._all.create(tenant=setup['other_tenant'], name='S2', duration=45, price='200.00')

        assert Service.objects.for_tenant(setup['tenant']).count() == 1
        assert Service.objects.for_tenant(setup['other_tenant']).count() == 1

    def test_unauthenticated_cannot_list(self):
        client = APIClient()
        # No host → tenant=None → middleware exempts localhost, DRF returns 401
        res = client.get('/rest/v1/catalog/services/')
        assert res.status_code == 401


# ── Schedule tests ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSchedule:
    URL = '/rest/v1/catalog/schedules/'

    def _make_doctor(self, tenant, user):
        return Doctor._all.create(tenant=tenant, user=user, appointment_duration=30)

    def test_create_schedule(self, setup):
        doctor = self._make_doctor(setup['tenant'], setup['staff'])
        client = auth_client(setup['owner'])
        res = client.post(
            self.URL,
            {
                'doctor': str(doctor.id),
                'weekday': 0,
                'start_time': '09:00:00',
                'end_time': '17:00:00',
            },
            format='json',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 201

    def test_invalid_time_range_returns_400(self, setup):
        doctor = self._make_doctor(setup['tenant'], setup['staff'])
        client = auth_client(setup['owner'])
        res = client.post(
            self.URL,
            {
                'doctor': str(doctor.id),
                'weekday': 1,
                'start_time': '17:00:00',
                'end_time': '09:00:00',
            },
            format='json',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 400

    def test_duplicate_weekday_per_doctor_fails(self, setup):
        doctor = self._make_doctor(setup['tenant'], setup['staff'])
        Schedule._all.create(
            tenant=setup['tenant'], doctor=doctor,
            weekday=0, start_time='09:00', end_time='17:00',
        )
        client = auth_client(setup['owner'])
        res = client.post(
            self.URL,
            {
                'doctor': str(doctor.id),
                'weekday': 0,
                'start_time': '10:00:00',
                'end_time': '15:00:00',
            },
            format='json',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 400

    def test_filter_schedules_by_doctor(self, setup):
        doctor1 = self._make_doctor(setup['tenant'], setup['staff'])
        doctor2_user = make_user('doc2@t.com')
        make_membership(setup['tenant'], doctor2_user, MembershipRole.DOCTOR)
        doctor2 = Doctor._all.create(tenant=setup['tenant'], user=doctor2_user)

        Schedule._all.create(tenant=setup['tenant'], doctor=doctor1, weekday=0, start_time='09:00', end_time='17:00')
        Schedule._all.create(tenant=setup['tenant'], doctor=doctor2, weekday=0, start_time='10:00', end_time='18:00')

        client = auth_client(setup['owner'])
        res = client.get(
            f'{self.URL}?doctor={doctor1.id}',
            HTTP_HOST=f"admin.{setup['tenant'].slug}.miapp.com",
        )
        assert res.status_code == 200
        assert res.data['count'] == 1
