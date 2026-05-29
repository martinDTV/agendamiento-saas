"""Tests del flujo de reseñas + agregados en discover/doctors/."""
from datetime import date, time, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Branch, Doctor, Service, Schedule
from apps.patients.models import Patient
from apps.reviews.models import Review
from apps.tenants.models import Tenant


User = get_user_model()


@pytest.fixture(autouse=True)
def reset_throttle_cache():
    """
    DRF throttling guarda contadores en cache. Si otros tests acumularon
    requests con la misma IP/anon scope, podemos disparar 429 falsos.
    Limpiar la caché antes de cada test asegura aislamiento.
    """
    from django.core.cache import cache
    cache.clear()
    yield


@pytest.fixture
def setup(db):
    tenant = Tenant.objects.create(slug='rev-clinic', name='Clínica Reviews')
    Branch._all.create(tenant=tenant, name='Sede')
    doctor_user = User.objects.create_user(
        username='dr@rev.com', email='dr@rev.com', password='x',
        first_name='Doctor', last_name='Review',
    )
    doctor = Doctor._all.create(
        tenant=tenant, user=doctor_user,
        specialty='Cardiología', appointment_duration=30,
    )
    service = Service._all.create(
        tenant=tenant, name='Consulta', duration=30, price=500,
    )
    service.doctors.add(doctor)
    return {'tenant': tenant, 'doctor': doctor, 'service': service}


def _make_patient(email='p@p.com', first_name='Pac', last_name='iente'):
    user = User.objects.create_user(
        username=email, email=email, password='Pass1234!',
        first_name=first_name, last_name=last_name, is_active=True,
    )
    return Patient.objects.create(user=user), user


def _auth_client(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


# ── Crear reseña ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreateReview:
    URL = '/rest/v1/reviews/'

    def test_authenticated_patient_can_create(self, setup):
        patient, user = _make_patient()
        client = _auth_client(user)
        res = client.post(self.URL, {
            'doctor': str(setup['doctor'].id),
            'rating': 5,
            'comment': 'Excelente atención.',
        }, format='json')
        assert res.status_code == 201, res.data
        assert res.data['rating'] == 5
        assert Review.objects.filter(patient=patient, doctor=setup['doctor']).count() == 1

    def test_unauthenticated_rejected(self, setup):
        client = APIClient()
        res = client.post(self.URL, {
            'doctor': str(setup['doctor'].id),
            'rating': 5,
        }, format='json')
        assert res.status_code == 401

    def test_user_without_patient_profile_rejected(self, setup):
        user = User.objects.create_user(
            username='staff@x.com', email='staff@x.com', password='x', is_active=True,
        )
        client = _auth_client(user)
        res = client.post(self.URL, {
            'doctor': str(setup['doctor'].id), 'rating': 4,
        }, format='json')
        assert res.status_code == 400

    def test_duplicate_review_rejected(self, setup):
        patient, user = _make_patient()
        Review.objects.create(patient=patient, doctor=setup['doctor'], rating=5)
        client = _auth_client(user)
        res = client.post(self.URL, {
            'doctor': str(setup['doctor'].id), 'rating': 3,
        }, format='json')
        assert res.status_code == 400

    def test_rating_out_of_range_rejected(self, setup):
        patient, user = _make_patient()
        client = _auth_client(user)
        # 6 (fuera de 1-5)
        res = client.post(self.URL, {
            'doctor': str(setup['doctor'].id), 'rating': 6,
        }, format='json')
        assert res.status_code == 400
        # 0 también
        res2 = client.post(self.URL, {
            'doctor': str(setup['doctor'].id), 'rating': 0,
        }, format='json')
        assert res2.status_code == 400


# ── Lista pública de reseñas por doctor ──────────────────────────────────────

@pytest.mark.django_db
class TestDoctorReviewsList:
    def test_lists_published_only(self, setup):
        p1, _ = _make_patient('a@p.com')
        p2, _ = _make_patient('b@p.com')
        Review.objects.create(patient=p1, doctor=setup['doctor'], rating=5, comment='Genial')
        Review.objects.create(patient=p2, doctor=setup['doctor'], rating=2, comment='Reportada',
                              is_published=False)
        client = APIClient()
        res = client.get(f'/rest/v1/public/reviews/doctor/{setup["doctor"].id}/')
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]['rating'] == 5


# ── Agregados en discover ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDiscoverAggregates:
    URL = '/rest/v1/public/discover/doctors/'

    def test_doctor_without_reviews_has_zero_count(self, setup):
        client = APIClient()
        res = client.get(self.URL)
        assert res.status_code == 200
        doc = next(d for d in res.data if d['id'] == str(setup['doctor'].id))
        assert doc['avg_rating'] is None
        assert doc['review_count'] == 0

    def test_doctor_with_reviews_returns_avg_and_count(self, setup):
        p1, _ = _make_patient('a@p.com')
        p2, _ = _make_patient('b@p.com')
        p3, _ = _make_patient('c@p.com')
        Review.objects.create(patient=p1, doctor=setup['doctor'], rating=5)
        Review.objects.create(patient=p2, doctor=setup['doctor'], rating=4)
        Review.objects.create(patient=p3, doctor=setup['doctor'], rating=3)

        client = APIClient()
        res = client.get(self.URL)
        assert res.status_code == 200
        doc = next(d for d in res.data if d['id'] == str(setup['doctor'].id))
        assert doc['avg_rating'] == 4.0  # (5+4+3)/3
        assert doc['review_count'] == 3

    def test_unpublished_review_excluded_from_aggregate(self, setup):
        p1, _ = _make_patient('a@p.com')
        p2, _ = _make_patient('b@p.com')
        Review.objects.create(patient=p1, doctor=setup['doctor'], rating=5)
        Review.objects.create(patient=p2, doctor=setup['doctor'], rating=1,
                              is_published=False)

        client = APIClient()
        res = client.get(self.URL)
        doc = next(d for d in res.data if d['id'] == str(setup['doctor'].id))
        # Solo cuenta la publicada
        assert doc['avg_rating'] == 5.0
        assert doc['review_count'] == 1

    def test_next_available_only_with_flag(self, setup):
        # Schedule del doctor para que get_next_available_slot encuentre algo
        Schedule._all.create(
            tenant=setup['tenant'], doctor=setup['doctor'],
            weekday=date.today().weekday(),
            start_time=time(9, 0), end_time=time(17, 0),
            is_active=True,
        )
        client = APIClient()

        # Sin flag → no se calcula
        res = client.get(self.URL)
        doc = next(d for d in res.data if d['id'] == str(setup['doctor'].id))
        assert doc['next_available'] is None

        # Con flag → se calcula
        res2 = client.get(self.URL, {'with_next_slot': 'true'})
        doc2 = next(d for d in res2.data if d['id'] == str(setup['doctor'].id))
        assert doc2['next_available'] is not None
        assert 'date' in doc2['next_available']
        assert 'start' in doc2['next_available']


# ── Reseñas anónimas con verificación de email ───────────────────────────────

@pytest.mark.django_db
class TestAnonymousReview:
    URL = '/rest/v1/public/reviews/'

    def test_creates_pending_review_and_sends_email(self, setup, settings):
        from django.core import mail
        from apps.reviews.models import PendingReview

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        mail.outbox = []

        client = APIClient()
        res = client.post(self.URL, {
            'doctor': str(setup['doctor'].id),
            'reviewer_name': 'Juan Pérez',
            'reviewer_email': 'juan@correo.com',
            'rating': 5,
            'comment': 'Excelente atención.',
        }, format='json')
        assert res.status_code == 201, res.data
        assert res.data['status'] == 'pending'

        # Se creó el PendingReview pero NO se publicó como Review
        pending = PendingReview.objects.get(reviewer_email='juan@correo.com')
        assert pending.rating == 5
        assert Review.objects.filter(reviewer_email='juan@correo.com').count() == 0

        # Se mandó el email de confirmación
        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert 'juan@correo.com' in msg.to
        assert str(pending.token) in msg.body

    def test_invalid_doctor_rejected(self, setup):
        from uuid import uuid4

        client = APIClient()
        res = client.post(self.URL, {
            'doctor': str(uuid4()),  # no existe
            'reviewer_name': 'Test',
            'reviewer_email': 'test@x.com',
            'rating': 5,
        }, format='json')
        assert res.status_code == 400

    def test_invalid_rating_rejected(self, setup):
        client = APIClient()
        res = client.post(self.URL, {
            'doctor': str(setup['doctor'].id),
            'reviewer_name': 'Test',
            'reviewer_email': 'test@x.com',
            'rating': 10,  # > 5
        }, format='json')
        assert res.status_code == 400

    def test_existing_published_review_blocks_new_anonymous(self, setup):
        """Si ya hay Review publicada con este email + doctor, rechaza."""
        Review.objects.create(
            doctor=setup['doctor'],
            patient=None,
            reviewer_name='Ya Existe',
            reviewer_email='ya@p.com',
            rating=5,
            is_published=True,
        )
        client = APIClient()
        res = client.post(self.URL, {
            'doctor': str(setup['doctor'].id),
            'reviewer_name': 'Ya Existe',
            'reviewer_email': 'ya@p.com',
            'rating': 3,
        }, format='json')
        assert res.status_code == 400

    def test_second_pending_replaces_first(self, setup, settings):
        """Si envías 2 reseñas anónimas sin confirmar, la 2da reemplaza la 1ra."""
        from django.core import mail
        from apps.reviews.models import PendingReview

        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        mail.outbox = []

        client = APIClient()
        payload = {
            'doctor': str(setup['doctor'].id),
            'reviewer_name': 'Cambio Opinión',
            'reviewer_email': 'cambio@p.com',
            'rating': 5,
        }
        client.post(self.URL, payload, format='json')
        # Segunda con rating distinto
        client.post(self.URL, {**payload, 'rating': 1}, format='json')

        # Solo hay UN pending (la segunda) con rating 1
        pendings = PendingReview.objects.filter(reviewer_email='cambio@p.com')
        assert pendings.count() == 1
        assert pendings.first().rating == 1


# ── Confirmación de reseña anónima ───────────────────────────────────────────

@pytest.mark.django_db
class TestConfirmReview:
    CREATE_URL = '/rest/v1/public/reviews/'
    CONFIRM_URL = '/rest/v1/public/reviews/confirm/'

    def _create_pending(self, setup, email='anon@p.com', rating=5):
        client = APIClient()
        client.post(self.CREATE_URL, {
            'doctor': str(setup['doctor'].id),
            'reviewer_name': 'Anon User',
            'reviewer_email': email,
            'rating': rating,
            'comment': 'Test',
        }, format='json')
        from apps.reviews.models import PendingReview
        return PendingReview.objects.get(reviewer_email=email)

    def test_post_confirms_publishes_review(self, setup, settings):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        pending = self._create_pending(setup)
        client = APIClient()
        res = client.post(self.CONFIRM_URL, {'token': str(pending.token)}, format='json')
        assert res.status_code == 200
        assert res.data['status'] == 'confirmed'

        # Ahora SÍ hay una Review publicada
        rev = Review.objects.filter(reviewer_email='anon@p.com', is_published=True).first()
        assert rev is not None
        assert rev.rating == 5
        assert rev.patient is None  # anónima

        # El pending quedó marcado como confirmado
        pending.refresh_from_db()
        assert pending.confirmed_at is not None
        assert pending.confirmed_review == rev

    def test_get_confirms_returns_html(self, setup, settings):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        pending = self._create_pending(setup)
        client = APIClient()
        res = client.get(self.CONFIRM_URL, {'token': str(pending.token)})
        assert res.status_code == 200
        assert b'<html' in res.content.lower() or b'<!doctype' in res.content.lower()
        assert b'publicada' in res.content.lower()

    def test_token_cannot_be_reused(self, setup, settings):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        pending = self._create_pending(setup)
        client = APIClient()
        # Primera confirmación OK
        res1 = client.post(self.CONFIRM_URL, {'token': str(pending.token)}, format='json')
        assert res1.status_code == 200
        # Segunda rechaza
        res2 = client.post(self.CONFIRM_URL, {'token': str(pending.token)}, format='json')
        assert res2.status_code == 400

    def test_invalid_token_returns_400(self, setup):
        from uuid import uuid4
        client = APIClient()
        res = client.post(self.CONFIRM_URL, {'token': str(uuid4())}, format='json')
        assert res.status_code == 400

    def test_get_without_token_returns_html_400(self, setup):
        client = APIClient()
        res = client.get(self.CONFIRM_URL)
        assert res.status_code == 400
        assert b'<html' in res.content.lower() or b'<!doctype' in res.content.lower()

    def test_confirmed_review_aggregates_into_doctor_rating(self, setup, settings):
        """La reseña anónima confirmada SÍ cuenta en avg_rating del discover."""
        settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
        pending = self._create_pending(setup, rating=4)
        client = APIClient()
        client.post(self.CONFIRM_URL, {'token': str(pending.token)}, format='json')

        # Verificar que aparece en el endpoint discover
        res = client.get('/rest/v1/public/discover/doctors/')
        doc = next(d for d in res.data if d['id'] == str(setup['doctor'].id))
        assert doc['avg_rating'] == 4.0
        assert doc['review_count'] == 1


# ── author_display_name (Patient o reviewer_name o "Anónimo") ────────────────

@pytest.mark.django_db
class TestAuthorDisplayName:
    def test_with_patient_uses_full_name(self, setup):
        patient, _ = _make_patient('john@p.com', first_name='John', last_name='Doe')
        rev = Review.objects.create(patient=patient, doctor=setup['doctor'], rating=5)
        assert rev.author_display_name == 'John Doe'

    def test_anonymous_uses_reviewer_name(self, setup):
        rev = Review.objects.create(
            patient=None,
            reviewer_name='María García',
            reviewer_email='maria@p.com',
            doctor=setup['doctor'], rating=4,
        )
        assert rev.author_display_name == 'María García'

    def test_falls_back_to_anonimo(self, setup):
        rev = Review.objects.create(
            patient=None,
            reviewer_name='',
            reviewer_email='',
            doctor=setup['doctor'], rating=3,
        )
        assert rev.author_display_name == 'Anónimo'
