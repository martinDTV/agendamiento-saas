"""
Tests del flujo completo de paciente:
  register → activate → login → reservar cita (autenticado) → ver mis citas.

También cubre que un paciente sin cuenta sigue pudiendo reservar (backward compat).
"""
from datetime import date, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.bookings.models import Appointment
from apps.catalog.models import Branch, Doctor, Service
from apps.patients.models import Patient, PatientActivationToken
from apps.tenants.models import Tenant


User = get_user_model()


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def tenant(db):
    return Tenant.objects.create(slug='clinica-test', name='Clínica Test')


@pytest.fixture
def doctor(tenant):
    user = User.objects.create_user(
        username='dra@test.com',
        email='dra@test.com',
        password='x',
        first_name='Ana',
        last_name='García',
    )
    branch = Branch._all.create(tenant=tenant, name='Sede')
    return Doctor._all.create(
        tenant=tenant,
        user=user,
        specialty='Medicina general',
        appointment_duration=30,
    )


@pytest.fixture
def service(tenant):
    return Service._all.create(
        tenant=tenant,
        name='Consulta general',
        duration=30,
        price=500,
    )


# ── Registro y activación ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPatientRegister:
    URL = '/rest/v1/public/patients/register/'

    def test_register_creates_inactive_user_and_patient(self, tenant):
        client = APIClient()
        res = client.post(
            self.URL,
            {
                'email': 'juan@paciente.com',
                'password': 'Secreta123!',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'phone': '+52 55 1234 5678',  # se normaliza a "5512345678"
            },
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 201
        assert res.data['email'] == 'juan@paciente.com'

        user = User.objects.get(email='juan@paciente.com')
        assert user.is_active is False  # debe activar
        assert user.first_name == 'Juan'

        patient = Patient.objects.get(user=user)
        # El serializer normaliza el teléfono a 10 dígitos crudos (ver validators.py).
        assert patient.phone == '5512345678'

        # Token de activación creado
        assert PatientActivationToken.objects.filter(user=user, used_at__isnull=True).exists()

    def test_register_duplicate_email_fails(self, tenant):
        User.objects.create_user(username='dup@p.com', email='dup@p.com', password='x')
        client = APIClient()
        res = client.post(
            self.URL,
            {'email': 'dup@p.com', 'password': 'Secreta123!', 'first_name': 'X'},
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 400

    def test_register_short_password_fails(self, tenant):
        client = APIClient()
        res = client.post(
            self.URL,
            {'email': 'short@p.com', 'password': 'abc', 'first_name': 'X'},
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 400


@pytest.mark.django_db
class TestPatientActivation:
    REGISTER_URL = '/rest/v1/public/patients/register/'
    ACTIVATE_URL = '/rest/v1/public/patients/activate/'

    def _register(self, tenant, email='maria@p.com'):
        client = APIClient()
        client.post(
            self.REGISTER_URL,
            {'email': email, 'password': 'Secreta123!', 'first_name': 'María'},
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        return PatientActivationToken.objects.get(user__email=email)

    def test_activate_with_valid_token(self, tenant):
        token = self._register(tenant)
        client = APIClient()
        res = client.post(
            self.ACTIVATE_URL,
            {'token': str(token.token)},
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 200
        token.refresh_from_db()
        assert token.used_at is not None
        assert token.user.is_active is True

    def test_activate_with_invalid_token_fails(self, tenant):
        import uuid
        client = APIClient()
        res = client.post(
            self.ACTIVATE_URL,
            {'token': str(uuid.uuid4())},
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 400

    def test_get_activation_returns_html_and_activates(self, tenant):
        """Click desde el botón del correo → GET con ?token=... → activa y HTML."""
        token = self._register(tenant, email='get@p.com')
        client = APIClient()
        res = client.get(
            f'{self.ACTIVATE_URL}?token={token.token}',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 200
        assert b'<html' in res.content.lower() or b'<!doctype' in res.content.lower()
        assert b'activada' in res.content.lower()
        token.refresh_from_db()
        assert token.used_at is not None
        assert token.user.is_active is True

    def test_get_activation_without_token_returns_html_400(self, tenant):
        client = APIClient()
        res = client.get(self.ACTIVATE_URL, HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 400
        assert b'<html' in res.content.lower() or b'<!doctype' in res.content.lower()

    def test_get_activation_with_invalid_token_returns_html_400(self, tenant):
        import uuid
        client = APIClient()
        res = client.get(
            f'{self.ACTIVATE_URL}?token={uuid.uuid4()}',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 400
        # Debe ser HTML (no JSON), porque el cliente es un navegador
        assert b'<html' in res.content.lower() or b'<!doctype' in res.content.lower()

    def test_token_cannot_be_reused(self, tenant):
        token = self._register(tenant)
        client = APIClient()
        # Primera activación: OK
        res1 = client.post(self.ACTIVATE_URL, {'token': str(token.token)}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res1.status_code == 200
        # Segunda: rechaza
        res2 = client.post(self.ACTIVATE_URL, {'token': str(token.token)}, format='json',
                           HTTP_X_TENANT_SLUG=tenant.slug)
        assert res2.status_code == 400


# ── Perfil ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPatientMe:
    URL = '/rest/v1/patients/me/'

    def _make_active_patient(self, email='active@p.com'):
        user = User.objects.create_user(
            username=email, email=email, password='Pass1234!',
            first_name='Activa', last_name='Paciente', is_active=True,
        )
        patient = Patient.objects.create(user=user, phone='5598765432')
        return user, patient

    def _auth_client(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return client

    def test_get_me_returns_full_profile(self, tenant):
        user, patient = self._make_active_patient()
        client = self._auth_client(user)
        res = client.get(self.URL, HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200
        assert res.data['email'] == user.email
        assert res.data['phone'] == '5598765432'
        assert res.data['first_name'] == 'Activa'

    def test_patch_me_updates_clinical_fields(self, tenant):
        user, patient = self._make_active_patient()
        client = self._auth_client(user)
        res = client.patch(
            self.URL,
            {
                'blood_type': 'O+',
                'allergies': 'Penicilina',
                'phone': '+52 55 9999 0000',  # 10 dígitos después de normalizar
                'curp': 'ABCD801010HDFRRR01',
            },
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 200, res.data
        patient.refresh_from_db()
        assert patient.blood_type == 'O+'
        assert patient.allergies == 'Penicilina'
        assert patient.phone == '5599990000'
        assert patient.curp == 'ABCD801010HDFRRR01'

    def test_me_without_auth_returns_401(self, tenant):
        client = APIClient()
        res = client.get(self.URL, HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 401

    def test_user_without_patient_profile_returns_404(self, tenant):
        # User staff sin perfil de paciente
        staff = User.objects.create_user(
            username='staff@c.com', email='staff@c.com', password='x', is_active=True,
        )
        client = self._auth_client(staff)
        res = client.get(self.URL, HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 404


# ── Booking público + Patient autenticado ────────────────────────────────────

@pytest.mark.django_db
class TestBookingLinksPatient:
    """Cuando un paciente autenticado reserva, Appointment.patient debe vincularse."""
    URL = '/rest/v1/public/appointments/'

    def _make_active_patient(self, email='booker@p.com'):
        user = User.objects.create_user(
            username=email, email=email, password='Pass1234!',
            first_name='Reservante', is_active=True,
        )
        patient = Patient.objects.create(user=user, phone='+52 55')
        return user, patient

    def _auth_client(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return client

    def _booking_payload(self, doctor, service, target_date):
        return {
            'doctor': doctor.id,
            'service': service.id,
            'patient_name': 'Reservante',
            'patient_email': 'booker@p.com',
            'patient_phone': '+52 55',
            'date': target_date.isoformat(),
            'start_time': '10:00',
        }

    def test_authenticated_patient_books_links_fk(self, tenant, doctor, service):
        """Reservar con JWT → Appointment.patient queda vinculado."""
        # Necesitamos un schedule del doctor para que el slot exista — pero el
        # serializer no valida slots disponibles por sí mismo (la validación
        # de overlap sí). Aquí solo verificamos el vínculo FK.
        user, patient = self._make_active_patient()
        client = self._auth_client(user)
        target = date.today() + timedelta(days=7)
        res = client.post(
            self.URL,
            self._booking_payload(doctor, service, target),
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 201, res.data
        appt = Appointment._all.get(pk=res.data['id'])
        assert appt.patient_id == patient.id
        assert appt.patient_email == 'booker@p.com'  # fallback strings se mantienen

    def test_anonymous_booking_keeps_patient_null(self, tenant, doctor, service):
        """Reservar SIN cuenta sigue funcionando — Appointment.patient queda None."""
        client = APIClient()
        target = date.today() + timedelta(days=7)
        res = client.post(
            self.URL,
            {
                'doctor': doctor.id,
                'service': service.id,
                'patient_name': 'Anónimo',
                'patient_email': 'anon@p.com',
                'patient_phone': '+52 0',
                'date': target.isoformat(),
                'start_time': '11:00',
            },
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 201, res.data
        appt = Appointment._all.get(pk=res.data['id'])
        assert appt.patient_id is None


# ── Mis citas (cross-tenant) ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestMyAppointments:
    URL = '/rest/v1/patients/me/appointments/'

    def _auth_client(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return client

    def test_returns_appointments_across_tenants(self, tenant, doctor, service):
        """El paciente ve sus citas de CUALQUIER clínica donde reservó."""
        # Crear segundo tenant + doctor + servicio
        other_tenant = Tenant.objects.create(slug='otra', name='Otra')
        other_doctor_user = User.objects.create_user(
            username='dr2@t.com', email='dr2@t.com', password='x',
            first_name='Otro', last_name='Doc',
        )
        Branch._all.create(tenant=other_tenant, name='S')
        other_doctor = Doctor._all.create(
            tenant=other_tenant, user=other_doctor_user,
            specialty='Otra', appointment_duration=30,
        )
        other_service = Service._all.create(
            tenant=other_tenant, name='Otra consulta', duration=30, price=500,
        )

        user = User.objects.create_user(
            username='cross@p.com', email='cross@p.com',
            password='x', first_name='Cross', is_active=True,
        )
        patient = Patient.objects.create(user=user)

        # Una cita en cada tenant
        Appointment._all.create(
            tenant=tenant, doctor=doctor, service=service, patient=patient,
            patient_name='C', patient_email='cross@p.com',
            date=date.today() + timedelta(days=5), start_time=time(10, 0),
            end_time=time(10, 30),
        )
        Appointment._all.create(
            tenant=other_tenant, doctor=other_doctor, service=other_service,
            patient=patient,
            patient_name='C', patient_email='cross@p.com',
            date=date.today() + timedelta(days=6), start_time=time(11, 0),
            end_time=time(11, 30),
        )

        client = self._auth_client(user)
        # El header X-Tenant-Slug es opcional aquí (Patient es global) pero la
        # request DEBE poder hacerse sin importar el tenant del header.
        res = client.get(self.URL, HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 200, res.data
        assert len(res.data) == 2
        # Ambas vienen con tenant_slug para que la app móvil sepa de qué clínica
        slugs = {appt['tenant_slug'] for appt in res.data}
        assert slugs == {'clinica-test', 'otra'}

    def test_my_appointments_requires_auth(self, tenant):
        client = APIClient()
        res = client.get(self.URL, HTTP_X_TENANT_SLUG=tenant.slug)
        assert res.status_code == 401


# ── Email de activación ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestActivationEmail:
    """
    Regresión del bug donde el correo mostraba dos enlaces idénticos
    (deep-link y "fallback web") porque SITE_URL no estaba configurado.
    """
    REGISTER_URL = '/rest/v1/public/patients/register/'

    def test_email_contains_distinct_web_link_and_deep_link(self, tenant, settings):
        from django.core import mail

        settings.SITE_URL = 'https://api.example.com'
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        mail.outbox = []

        client = APIClient()
        res = client.post(
            self.REGISTER_URL,
            {'email': 'mailcheck@p.com', 'password': 'Secreta123!', 'first_name': 'Mail'},
            format='json',
            HTTP_X_TENANT_SLUG=tenant.slug,
        )
        assert res.status_code == 201
        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        text_body = msg.body
        # Debe haber un link web HTTP (no agendamiento://) que apunte al endpoint
        # GET de activación.
        assert 'https://api.example.com/rest/v1/public/patients/activate/?token=' in text_body
        # El deep-link también debe estar, pero como SECUNDARIO.
        assert 'agendamiento://activate?token=' in text_body
        # Ambos enlaces deben ser DISTINTOS (no como el bug original).
        import re
        urls = re.findall(r'(https?://\S+|agendamiento://\S+)', text_body)
        urls_clean = [u.rstrip('.,)') for u in urls]
        assert len(set(urls_clean)) >= 2, f'Esperaba 2+ URLs distintas, vi: {urls_clean}'

        # Versión HTML adjuntada
        assert len(msg.alternatives) == 1
        html_body, mimetype = msg.alternatives[0]
        assert mimetype == 'text/html'
        assert 'Activar mi cuenta' in html_body
        assert 'https://api.example.com/rest/v1/public/patients/activate/' in html_body
