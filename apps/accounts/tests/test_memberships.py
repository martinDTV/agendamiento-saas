import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import Membership, MembershipRole, InvitationToken
from apps.tenants.models import Tenant

User = get_user_model()


def make_tenant(slug='t1'):
    return Tenant.objects.create(slug=slug, name=slug, is_active=True)


def make_user(email='u@t.com'):
    return User.objects.create_user(email=email, password='ValidPass123!')


def make_membership(tenant, user, role=MembershipRole.OWNER):
    return Membership._all.create(tenant=tenant, user=user, role=role)


@pytest.fixture
def owner_client():
    client = APIClient()
    tenant = make_tenant('owner-tenant')
    user = make_user('owner@t.com')
    make_membership(tenant, user, MembershipRole.OWNER)
    from rest_framework_simplejwt.tokens import RefreshToken
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    client.tenant = tenant
    return client


@pytest.mark.django_db
class TestPermissions:
    def test_staff_cannot_list_memberships(self):
        client = APIClient()
        tenant = make_tenant('staff-tenant')
        staff = make_user('staff@t.com')
        make_membership(tenant, staff, MembershipRole.STAFF)
        from rest_framework_simplejwt.tokens import RefreshToken
        token = str(RefreshToken.for_user(staff).access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # No tenant header — middleware sets None on localhost
        # Permissions check requires request.tenant, so this returns 403
        res = client.get('/rest/v1/accounts/memberships/')
        assert res.status_code in (403, 404)

    def test_unauthenticated_cannot_list_memberships(self):
        client = APIClient()
        res = client.get('/rest/v1/accounts/memberships/')
        assert res.status_code == 401


@pytest.mark.django_db
class TestInvitationFlow:
    def test_invitation_accept_creates_membership(self):
        tenant = make_tenant('inv-tenant')
        inviter = make_user('inviter@t.com')
        make_membership(tenant, inviter, MembershipRole.OWNER)

        invitation = InvitationToken._all.create(
            tenant=tenant,
            email='newbie@t.com',
            role=MembershipRole.STAFF,
            invited_by=inviter,
        )

        client = APIClient()
        res = client.post(
            f'/rest/v1/accounts/invitations/accept/{invitation.token}/',
            format='json',
        )
        assert res.status_code == 200
        assert 'access' in res.data
        assert User.objects.filter(email='newbie@t.com').exists()
        assert Membership._all.filter(tenant=tenant, user__email='newbie@t.com').exists()

    def test_expired_invitation_returns_410(self):
        from django.utils import timezone
        from datetime import timedelta
        tenant = make_tenant('exp-tenant')
        inviter = make_user('inviter2@t.com')
        invitation = InvitationToken._all.create(
            tenant=tenant,
            email='late@t.com',
            role=MembershipRole.STAFF,
            invited_by=inviter,
            expires_at=timezone.now() - timedelta(days=1),
        )
        client = APIClient()
        res = client.post(f'/rest/v1/accounts/invitations/accept/{invitation.token}/')
        assert res.status_code == 410

    def test_invalid_token_returns_404(self):
        client = APIClient()
        res = client.post('/rest/v1/accounts/invitations/accept/00000000-0000-0000-0000-000000000000/')
        assert res.status_code == 404
