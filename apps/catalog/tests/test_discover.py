"""
Tests del flujo cross-clínica (discover endpoints + booking sin X-Tenant-Slug).

Cubre la promesa de la opción B (Patient global): un paciente puede ver y
reservar en cualquier clínica del SaaS desde la misma cuenta.
"""
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Branch, Doctor, Service
from apps.tenants.models import Tenant


User = get_user_model()


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def two_tenants(db):
    """Dos clínicas activas, cada una con un doctor y un servicio."""
    t_a = Tenant.objects.create(slug='cross-a', name='Clínica Cross A')
    t_b = Tenant.objects.create(slug='cross-b', name='Clínica Cross B')

    user_a = User.objects.create_user(
        username='doctora@a.com', email='doctora@a.com', password='x',
        first_name='Ana', last_name='Pérez',
    )
    user_b = User.objects.create_user(
        username='doctorb@b.com', email='doctorb@b.com', password='x',
        first_name='Beto', last_name='Gómez',
    )

    Branch._all.create(tenant=t_a, name='Sede A')
    Branch._all.create(tenant=t_b, name='Sede B')

    doc_a = Doctor._all.create(
        tenant=t_a, user=user_a, specialty='Cardiología', appointment_duration=30,
    )
    doc_b = Doctor._all.create(
        tenant=t_b, user=user_b, specialty='Dermatología', appointment_duration=30,
    )

    svc_a = Service._all.create(tenant=t_a, name='Consulta cardiología', duration=30, price=800)
    svc_b = Service._all.create(tenant=t_b, name='Consulta dermatología', duration=30, price=700)
    svc_a.doctors.add(doc_a)
    svc_b.doctors.add(doc_b)

    return {
        't_a': t_a, 't_b': t_b,
        'doc_a': doc_a, 'doc_b': doc_b,
        'svc_a': svc_a, 'svc_b': svc_b,
    }


# ── /public/discover/doctors/ ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestDiscoverDoctors:
    URL = '/rest/v1/public/discover/doctors/'

    def test_returns_doctors_from_all_tenants_without_header(self, two_tenants):
        """SIN X-Tenant-Slug y SIN Host de subdominio → devuelve doctores de TODAS."""
        client = APIClient()
        res = client.get(self.URL)  # ← sin headers
        assert res.status_code == 200
        tenant_slugs = {d['tenant_slug'] for d in res.data}
        assert tenant_slugs == {'cross-a', 'cross-b'}

    def test_each_doctor_has_tenant_info(self, two_tenants):
        client = APIClient()
        res = client.get(self.URL)
        assert res.status_code == 200
        for d in res.data:
            assert 'tenant_slug' in d
            assert 'tenant_name' in d
            assert 'full_name' in d
            assert 'specialty' in d

    def test_filter_by_tenant_slug(self, two_tenants):
        client = APIClient()
        res = client.get(self.URL, {'tenant': 'cross-a'})
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['tenant_slug'] == 'cross-a'

    def test_filter_by_specialty(self, two_tenants):
        client = APIClient()
        res = client.get(self.URL, {'specialty': 'cardio'})
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['specialty'] == 'Cardiología'

    def test_search_by_doctor_name(self, two_tenants):
        client = APIClient()
        res = client.get(self.URL, {'q': 'Beto'})
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['tenant_slug'] == 'cross-b'

    def test_inactive_doctors_not_returned(self, two_tenants):
        two_tenants['doc_a'].is_active = False
        two_tenants['doc_a'].save()
        client = APIClient()
        res = client.get(self.URL)
        assert res.status_code == 200
        slugs = {d['tenant_slug'] for d in res.data}
        assert slugs == {'cross-b'}

    def test_inactive_tenant_doctors_not_returned(self, two_tenants):
        two_tenants['t_b'].is_active = False
        two_tenants['t_b'].save()
        client = APIClient()
        res = client.get(self.URL)
        assert res.status_code == 200
        slugs = {d['tenant_slug'] for d in res.data}
        assert slugs == {'cross-a'}


# ── /public/discover/clinics/ ────────────────────────────────────────────────

@pytest.mark.django_db
class TestDiscoverClinics:
    URL = '/rest/v1/public/discover/clinics/'

    def test_returns_all_active_clinics(self, two_tenants):
        client = APIClient()
        res = client.get(self.URL)
        assert res.status_code == 200
        slugs = {c['slug'] for c in res.data}
        assert slugs == {'cross-a', 'cross-b'}

    def test_each_clinic_has_doctor_count(self, two_tenants):
        client = APIClient()
        res = client.get(self.URL)
        for c in res.data:
            assert 'doctor_count' in c
            assert c['doctor_count'] >= 1


# ── /public/discover/services/?doctor=<id> ──────────────────────────────────

@pytest.mark.django_db
class TestDiscoverServices:
    URL = '/rest/v1/public/discover/services/'

    def test_returns_services_for_doctor_without_header(self, two_tenants):
        client = APIClient()
        res = client.get(self.URL, {'doctor': two_tenants['doc_a'].id})
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['name'] == 'Consulta cardiología'

    def test_empty_without_doctor_param(self, two_tenants):
        client = APIClient()
        res = client.get(self.URL)
        assert res.status_code == 200
        assert res.data == []


# ── Slots y booking sin X-Tenant-Slug ────────────────────────────────────────

@pytest.mark.django_db
class TestCrossTenantSlots:
    URL = '/rest/v1/public/slots/'

    def test_slots_work_without_tenant_header(self, two_tenants):
        """SIN header — el tenant se deduce del doctor enviado."""
        client = APIClient()
        future = (date.today() + timedelta(days=7)).isoformat()
        res = client.get(self.URL, {
            'doctor': two_tenants['doc_a'].id,
            'service': two_tenants['svc_a'].id,
            'date': future,
        })
        assert res.status_code == 200
        assert 'slots' in res.data

    def test_slots_reject_doctor_from_different_tenant(self, two_tenants):
        """Doctor de A + service de B → 404 (mismatch)."""
        client = APIClient()
        future = (date.today() + timedelta(days=7)).isoformat()
        res = client.get(self.URL, {
            'doctor': two_tenants['doc_a'].id,
            'service': two_tenants['svc_b'].id,
            'date': future,
        })
        assert res.status_code == 404


@pytest.mark.django_db
class TestCrossTenantBooking:
    URL = '/rest/v1/public/appointments/'

    def _payload(self, doctor, service, target_date):
        return {
            'doctor': doctor.id,
            'service': service.id,
            'patient_name': 'Cross Patient',
            'patient_email': 'cross@p.com',
            'patient_phone': '+52 55 1234 5678',
            'date': target_date.isoformat(),
            'start_time': '10:00',
        }

    def test_book_in_tenant_a_without_header(self, two_tenants):
        client = APIClient()
        target = date.today() + timedelta(days=7)
        res = client.post(
            self.URL,
            self._payload(two_tenants['doc_a'], two_tenants['svc_a'], target),
            format='json',
        )  # ← sin X-Tenant-Slug
        assert res.status_code == 201, res.data
        assert res.data['tenant_slug'] == 'cross-a'

    def test_book_in_tenant_b_without_header(self, two_tenants):
        client = APIClient()
        target = date.today() + timedelta(days=7)
        res = client.post(
            self.URL,
            self._payload(two_tenants['doc_b'], two_tenants['svc_b'], target),
            format='json',
        )
        assert res.status_code == 201, res.data
        assert res.data['tenant_slug'] == 'cross-b'

    def test_book_rejects_doctor_service_mismatch(self, two_tenants):
        """Doctor de A + service de B → 400."""
        client = APIClient()
        target = date.today() + timedelta(days=7)
        res = client.post(
            self.URL,
            self._payload(two_tenants['doc_a'], two_tenants['svc_b'], target),
            format='json',
        )
        assert res.status_code == 400

    def test_book_rejects_invalid_doctor(self, two_tenants):
        client = APIClient()
        target = date.today() + timedelta(days=7)
        res = client.post(
            self.URL,
            {
                'doctor': 99999,
                'service': two_tenants['svc_a'].id,
                'patient_name': 'X',
                'patient_email': 'x@p.com',
                'patient_phone': '5511112222',
                'date': target.isoformat(),
                'start_time': '10:00',
            },
            format='json',
        )
        assert res.status_code == 400
