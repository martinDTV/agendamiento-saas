import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import Membership, MembershipRole
from apps.tenants.models import Tenant

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def registration_payload():
    return {
        'tenant_name': 'Clínica López',
        'tenant_slug': 'clinica-lopez',
        'tenant_type': 'solo',
        'email': 'dr.lopez@ejemplo.com',
        'password': 'S3gura!Pass123',
        'first_name': 'Carlos',
        'last_name': 'López',
    }


@pytest.mark.django_db
class TestTenantRegistration:
    URL = '/rest/v1/accounts/register/'

    def test_creates_tenant_user_and_owner_membership(self, client, registration_payload):
        res = client.post(self.URL, registration_payload, format='json')
        assert res.status_code == 201

        assert Tenant.objects.filter(slug='clinica-lopez').exists()
        user = User.objects.get(email='dr.lopez@ejemplo.com')
        tenant = Tenant.objects.get(slug='clinica-lopez')
        membership = Membership.objects.for_tenant(tenant).get(user=user)
        assert membership.role == MembershipRole.OWNER

    def test_returns_tokens_and_tenant(self, client, registration_payload):
        res = client.post(self.URL, registration_payload, format='json')
        assert 'access' in res.data
        assert 'refresh' in res.data
        assert res.data['tenant']['slug'] == 'clinica-lopez'

    def test_duplicate_slug_returns_400(self, client, registration_payload):
        client.post(self.URL, registration_payload, format='json')
        payload2 = {**registration_payload, 'email': 'otro@ejemplo.com'}
        res = client.post(self.URL, payload2, format='json')
        assert res.status_code == 400

    def test_duplicate_email_returns_400(self, client, registration_payload):
        client.post(self.URL, registration_payload, format='json')
        payload2 = {**registration_payload, 'tenant_slug': 'otro-slug'}
        res = client.post(self.URL, payload2, format='json')
        assert res.status_code == 400

    def test_invalid_password_returns_400(self, client, registration_payload):
        registration_payload['password'] = '123'
        res = client.post(self.URL, registration_payload, format='json')
        assert res.status_code == 400


@pytest.mark.django_db
class TestMeEndpoint:
    URL = '/rest/v1/accounts/me/'

    def _register_and_login(self, client):
        payload = {
            'tenant_name': 'Test Clinic',
            'tenant_slug': 'test-clinic',
            'tenant_type': 'solo',
            'email': 'owner@test.com',
            'password': 'ValidPass123!',
        }
        res = client.post('/rest/v1/accounts/register/', payload, format='json')
        return res.data['access']

    def test_me_returns_user_and_memberships(self, client):
        token = self._register_and_login(client)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = client.get(self.URL)
        assert res.status_code == 200
        assert res.data['email'] == 'owner@test.com'
        assert len(res.data['memberships']) == 1
        assert res.data['memberships'][0]['role'] == MembershipRole.OWNER

    def test_me_requires_authentication(self, client):
        res = client.get(self.URL)
        assert res.status_code == 401
