"""Tests del flujo geográfico: geocoding, distancia haversine, endpoint."""
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Branch, Doctor, Service
from apps.places.clients import GeocodeResult
from apps.places.geo import haversine_km, parse_latlng
from apps.tenants.models import Tenant


User = get_user_model()


# ── Haversine ────────────────────────────────────────────────────────────────

class TestHaversine:
    def test_zero_distance_when_same_point(self):
        assert haversine_km(19.43, -99.16, 19.43, -99.16) == pytest.approx(0, abs=0.01)

    def test_cdmx_to_monterrey_aprox(self):
        # CDMX (19.43, -99.13) → Monterrey (25.69, -100.32) ≈ 715 km
        d = haversine_km(19.43, -99.13, 25.69, -100.32)
        assert 700 < d < 730

    def test_palanca_de_signos_correcta(self):
        """Invertir el orden no cambia la distancia (simétrica)."""
        d1 = haversine_km(19.43, -99.16, 25.69, -100.32)
        d2 = haversine_km(25.69, -100.32, 19.43, -99.16)
        assert d1 == pytest.approx(d2, abs=0.01)


class TestParseLatLng:
    def test_valid_float(self):
        assert parse_latlng('19.43') == 19.43

    def test_negative(self):
        assert parse_latlng('-99.16') == -99.16

    def test_invalid(self):
        assert parse_latlng('abc') is None
        assert parse_latlng('') is None
        assert parse_latlng(None) is None

    def test_out_of_range(self):
        assert parse_latlng('200') is None  # > 180
        assert parse_latlng('-200') is None  # < -180


# ── Geocoding helper ─────────────────────────────────────────────────────────

class TestGeocodeAddress:
    def test_parses_google_response(self, settings):
        from apps.places.clients import geocode_address

        settings.GOOGLE_PLACES_API_KEY = 'fake-key'
        fake_response = {
            'places': [{
                'formattedAddress': 'Av. Reforma 222, CDMX',
                'location': {'latitude': 19.43, 'longitude': -99.16},
            }],
        }
        with patch('apps.places.clients.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = fake_response
            result = geocode_address('Av. Reforma 222, CDMX')

        assert result is not None
        assert result.lat == 19.43
        assert result.lng == -99.16
        assert result.source == 'google'

    def test_no_api_key_returns_none(self, settings):
        from apps.places.clients import geocode_address

        settings.GOOGLE_PLACES_API_KEY = ''
        assert geocode_address('Av. Reforma 222') is None

    def test_empty_address_returns_none(self, settings):
        from apps.places.clients import geocode_address

        settings.GOOGLE_PLACES_API_KEY = 'fake-key'
        assert geocode_address('') is None
        assert geocode_address('   ') is None

    def test_no_results_returns_none(self, settings):
        from apps.places.clients import geocode_address

        settings.GOOGLE_PLACES_API_KEY = 'fake-key'
        with patch('apps.places.clients.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'places': []}
            assert geocode_address('NoExiste 12345') is None


# ── Endpoint /public/places/branch/{id}/location/ ──────────────────────────

@pytest.mark.django_db
class TestBranchLocationEndpoint:
    def _create_branch(self, address='Av. Reforma 222', lat=None, lng=None):
        tenant = Tenant.objects.create(slug='geo-t', name='Geo Test')
        return Branch._all.create(
            tenant=tenant, name='Sede', address=address,
            address_lat=lat, address_lng=lng,
        )

    def _url(self, branch_id):
        return f'/rest/v1/public/places/branch/{branch_id}/location/'

    def test_returns_cached_coords_if_present(self):
        b = self._create_branch(lat=19.43, lng=-99.16)
        client = APIClient()
        with patch('apps.places.views.geocode_address') as mock:
            res = client.get(self._url(b.id))
        assert res.status_code == 200
        assert res.data['lat'] == 19.43
        assert res.data['source'] == 'cache'
        mock.assert_not_called()  # NO debe llamar a Google

    def test_geocodes_on_demand_if_missing(self):
        b = self._create_branch(address='Av. Reforma 222, CDMX')
        client = APIClient()
        with patch('apps.places.views.geocode_address') as mock:
            mock.return_value = GeocodeResult(
                lat=19.43, lng=-99.16,
                formatted_address='Av. Reforma 222, CDMX',
            )
            res = client.get(self._url(b.id))
        assert res.status_code == 200
        assert res.data['lat'] == 19.43
        assert res.data['source'] == 'google'
        # Y se guardó en la branch
        b.refresh_from_db()
        assert b.address_lat == 19.43
        assert b.address_geocoded_at is not None

    def test_404_if_branch_missing(self):
        client = APIClient()
        res = client.get(self._url(uuid4()))
        assert res.status_code == 404

    def test_503_if_no_address(self):
        b = self._create_branch(address='')
        client = APIClient()
        res = client.get(self._url(b.id))
        assert res.status_code == 503


# ── Discover doctors con filtro de distancia ─────────────────────────────────

@pytest.mark.django_db
class TestDiscoverWithDistance:
    URL = '/rest/v1/public/discover/doctors/'

    def _setup_doctors_in_3_cities(self):
        """Crea 3 doctores: CDMX, Guadalajara, Monterrey."""
        # CDMX
        t1 = Tenant.objects.create(slug='cdmx', name='Clínica CDMX')
        b1 = Branch._all.create(
            tenant=t1, name='S', address='CDMX',
            address_lat=19.43, address_lng=-99.13,
        )
        u1 = User.objects.create_user(
            username='d1@x.com', email='d1@x.com', password='x',
            first_name='Cdmx', last_name='Doc',
        )
        d1 = Doctor._all.create(
            tenant=t1, user=u1, branch=b1, specialty='G', appointment_duration=30,
        )

        # GDL (≈530km de CDMX)
        t2 = Tenant.objects.create(slug='gdl', name='Clínica GDL')
        b2 = Branch._all.create(
            tenant=t2, name='S', address='GDL',
            address_lat=20.67, address_lng=-103.35,
        )
        u2 = User.objects.create_user(
            username='d2@x.com', email='d2@x.com', password='x',
            first_name='Gdl', last_name='Doc',
        )
        d2 = Doctor._all.create(
            tenant=t2, user=u2, branch=b2, specialty='G', appointment_duration=30,
        )

        # MTY (≈715km de CDMX)
        t3 = Tenant.objects.create(slug='mty', name='Clínica MTY')
        b3 = Branch._all.create(
            tenant=t3, name='S', address='MTY',
            address_lat=25.69, address_lng=-100.32,
        )
        u3 = User.objects.create_user(
            username='d3@x.com', email='d3@x.com', password='x',
            first_name='Mty', last_name='Doc',
        )
        d3 = Doctor._all.create(
            tenant=t3, user=u3, branch=b3, specialty='G', appointment_duration=30,
        )

        return {'cdmx': d1, 'gdl': d2, 'mty': d3}

    def test_without_latlng_returns_all_no_distance(self):
        self._setup_doctors_in_3_cities()
        client = APIClient()
        res = client.get(self.URL)
        assert res.status_code == 200
        assert len(res.data) == 3
        # Sin lat/lng, distance_km es None
        for d in res.data:
            assert d['distance_km'] is None

    def test_with_latlng_orders_by_distance(self):
        self._setup_doctors_in_3_cities()
        client = APIClient()
        # Usuario en CDMX, radio amplio para incluir GDL y MTY (no usar default 50km)
        res = client.get(self.URL, {
            'lat': '19.43', 'lng': '-99.13', 'radius_km': '2000',
        })
        assert res.status_code == 200
        # Ordenados: CDMX más cerca, GDL después, MTY al final
        slugs = [d['tenant_slug'] for d in res.data]
        assert slugs == ['cdmx', 'gdl', 'mty']
        # Todos tienen distance_km
        assert res.data[0]['distance_km'] == pytest.approx(0, abs=0.5)
        assert res.data[1]['distance_km'] < res.data[2]['distance_km']

    def test_radius_filters_out_far_doctors(self):
        self._setup_doctors_in_3_cities()
        client = APIClient()
        # Radio 100km desde CDMX → solo cdmx
        res = client.get(self.URL, {
            'lat': '19.43', 'lng': '-99.13', 'radius_km': '100',
        })
        assert res.status_code == 200
        slugs = [d['tenant_slug'] for d in res.data]
        assert slugs == ['cdmx']

    def test_no_branch_or_no_geocode_appears_last(self):
        """Doctor sin branch geocodificada va AL FINAL cuando hay lat/lng."""
        docs = self._setup_doctors_in_3_cities()
        # Borrar geocodificación de mty
        docs['mty'].branch.address_lat = None
        docs['mty'].branch.address_lng = None
        docs['mty'].branch.save()

        client = APIClient()
        res = client.get(self.URL, {
            'lat': '19.43', 'lng': '-99.13', 'radius_km': '1000',
        })
        assert res.status_code == 200
        # cdmx, gdl con distancia; mty al final con distance=None
        slugs = [d['tenant_slug'] for d in res.data]
        assert slugs == ['cdmx', 'gdl', 'mty']
        assert res.data[2]['distance_km'] is None
