"""
Tests de validación de formato MX para Patient.

Cubre:
  - CURP: longitud exacta 18, regex oficial RENAPO
  - RFC persona física: longitud exacta 13, regex SAT
  - Teléfono MX: 10 dígitos, normalización de espacios/+52/paréntesis
  - Código postal: 5 dígitos
  - Vacío (todos los campos son opcionales)

Los tests usan el endpoint real PATCH /patients/me/ para verificar end-to-end
que la validación SE DISPARA en el serializer + modelo, no solo unitariamente.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.patients.validators import (
    normalize_curp,
    normalize_phone_mx,
    normalize_rfc,
    normalize_zip_mx,
)


User = get_user_model()


@pytest.fixture
def tenant(db):
    from apps.tenants.models import Tenant
    return Tenant.objects.create(slug='clinica-val', name='Clínica Val')


@pytest.fixture
def patient_client(db, tenant):
    """Cliente autenticado con un Patient activo asociado."""
    user = User.objects.create_user(
        username='val@p.com', email='val@p.com', password='Pass1234!',
        first_name='Val', last_name='Idator', is_active=True,
    )
    Patient.objects.create(user=user)

    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client, user


# ── Normalización (unit) ─────────────────────────────────────────────────────

class TestNormalize:
    def test_curp_uppercase_strips_spaces(self):
        assert normalize_curp('  pepj 800101 hdfrrr01  ') == 'PEPJ800101HDFRRR01'

    def test_rfc_uppercase_strips_spaces(self):
        assert normalize_rfc('pepj 800101 ab1') == 'PEPJ800101AB1'

    def test_phone_strips_formatting(self):
        assert normalize_phone_mx('+52 55 1234 5678') == '5512345678'
        assert normalize_phone_mx('(55) 1234-5678') == '5512345678'
        assert normalize_phone_mx('52 5512345678') == '5512345678'
        assert normalize_phone_mx('5215512345678') == '5512345678'

    def test_zip_strips_non_digits(self):
        assert normalize_zip_mx('CP 06000') == '06000'
        assert normalize_zip_mx('06000-1234') == '060001234'  # devuelve sin formato

    def test_empty_inputs(self):
        assert normalize_curp('') == ''
        assert normalize_rfc(None or '') == ''
        assert normalize_phone_mx('') == ''
        assert normalize_zip_mx('') == ''


# ── CURP ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCURPValidation:
    URL = '/rest/v1/patients/me/'

    def test_valid_curp_passes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'curp': 'PEPJ800101HDFRRR01'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200, res.data
        assert res.data['curp'] == 'PEPJ800101HDFRRR01'

    def test_lowercase_with_spaces_normalizes_then_passes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(
            self.URL,
            {'curp': 'pepj 800101 hdfrrr01'},
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 200, res.data
        assert res.data['curp'] == 'PEPJ800101HDFRRR01'

    def test_too_short_curp_fails(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'curp': 'PEPJ800101H'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 400
        assert 'curp' in res.data

    def test_invalid_format_curp_fails(self, patient_client, tenant):
        # 18 chars pero no cumple el regex (sexo debe ser H/M en pos 11)
        client, _ = patient_client
        res = client.patch(self.URL, {'curp': 'PEPJ800101XDFRRR01'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 400
        assert 'curp' in res.data

    def test_random_garbage_curp_fails(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'curp': 'asdfghjkl'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 400
        assert 'curp' in res.data

    def test_empty_curp_allowed(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'curp': ''}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200


# ── RFC ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRFCValidation:
    URL = '/rest/v1/patients/me/'

    def test_valid_rfc_passes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'rfc': 'PEPJ800101AB1'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200, res.data
        assert res.data['rfc'] == 'PEPJ800101AB1'

    def test_lowercase_normalizes_then_passes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'rfc': 'pepj800101ab1'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200
        assert res.data['rfc'] == 'PEPJ800101AB1'

    def test_too_short_rfc_fails(self, patient_client, tenant):
        # 12 chars (formato persona moral) NO debe pasar — pacientes son
        # personas físicas, siempre 13.
        client, _ = patient_client
        res = client.patch(self.URL, {'rfc': 'ABC800101AB1'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 400
        assert 'rfc' in res.data

    def test_random_garbage_rfc_fails(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'rfc': '123ABC456DEF'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 400
        assert 'rfc' in res.data

    def test_empty_rfc_allowed(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'rfc': ''}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200


# ── Teléfono ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPhoneValidation:
    URL = '/rest/v1/patients/me/'

    def test_ten_digits_passes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'phone': '5512345678'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200
        assert res.data['phone'] == '5512345678'

    def test_with_lada_plus_52_normalizes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'phone': '+52 55 1234 5678'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200, res.data
        assert res.data['phone'] == '5512345678'

    def test_with_parentheses_and_dashes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'phone': '(55) 1234-5678'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200
        assert res.data['phone'] == '5512345678'

    def test_nine_digits_fails(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'phone': '551234567'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 400
        assert 'phone' in res.data

    def test_letters_in_phone_fail(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'phone': 'abc1234567'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 400
        assert 'phone' in res.data

    def test_empty_phone_allowed(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'phone': ''}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200


# ── Código postal ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestZipValidation:
    URL = '/rest/v1/patients/me/'

    def test_five_digits_passes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'address_zip': '06000'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200
        assert res.data['address_zip'] == '06000'

    def test_with_letters_normalizes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'address_zip': 'CP 06000'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200
        assert res.data['address_zip'] == '06000'

    def test_four_digits_fails(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(self.URL, {'address_zip': '0600'}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 400
        assert 'address_zip' in res.data


# ── Emergency phone ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEmergencyPhone:
    URL = '/rest/v1/patients/me/'

    def test_emergency_phone_normalizes(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(
            self.URL,
            {'emergency_contact_phone': '+52 (55) 9876-5432'},
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 200
        assert res.data['emergency_contact_phone'] == '5598765432'

    def test_emergency_phone_invalid_fails(self, patient_client, tenant):
        client, _ = patient_client
        res = client.patch(
            self.URL,
            {'emergency_contact_phone': '12345'},
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 400
        assert 'emergency_contact_phone' in res.data
