"""Tests del endpoint /public/places/postal-code/{cp}/."""
from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.places.clients import (
    PostalCodeInfo,
    PostalCodeNotFound,
    PostalCodeProviderError,
)


URL = '/rest/v1/public/places/postal-code/{cp}/'


@pytest.fixture(autouse=True)
def clear_cache_before_each():
    """Tests deben empezar con caché limpia (otros tests pueden haber dejado data)."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestPostalCodeLookup:
    def _ok_info(self, cp='06600'):
        return PostalCodeInfo(
            postal_code=cp,
            state='Ciudad de México',
            city='Ciudad de México',
            neighborhoods=['Juárez'],
            country='México',
            lat=19.385,
            lng=-99.165,
            source='zippopotam',
        )

    def test_valid_cp_returns_address_info(self):
        client = APIClient()
        with patch('apps.places.views.lookup_postal_code', return_value=self._ok_info()):
            res = client.get(URL.format(cp='06600'))
        assert res.status_code == 200
        data = res.json()
        assert data['postal_code'] == '06600'
        assert data['state'] == 'Ciudad de México'
        assert data['neighborhoods'] == ['Juárez']
        assert data['source'] == 'zippopotam'

    def test_invalid_format_returns_400(self):
        client = APIClient()
        # Solo 4 dígitos
        res = client.get(URL.format(cp='1234'))
        assert res.status_code == 400
        # Con letras
        res2 = client.get(URL.format(cp='abcde'))
        assert res2.status_code == 400

    def test_unknown_cp_returns_404(self):
        client = APIClient()
        with patch(
            'apps.places.views.lookup_postal_code',
            side_effect=PostalCodeNotFound('no existe'),
        ):
            res = client.get(URL.format(cp='99999'))
        assert res.status_code == 404
        assert 'detail' in res.json()

    def test_provider_error_returns_503(self):
        """Si ambos providers caen, devolvemos 503 (servicio dependiente)."""
        client = APIClient()
        with patch(
            'apps.places.views.lookup_postal_code',
            side_effect=PostalCodeProviderError('zippopotam down'),
        ):
            res = client.get(URL.format(cp='06600'))
        assert res.status_code == 503

    def test_response_is_cached(self):
        """Segunda llamada al mismo CP NO debe pegar a los providers."""
        client = APIClient()
        with patch(
            'apps.places.views.lookup_postal_code',
            return_value=self._ok_info(),
        ) as mock:
            client.get(URL.format(cp='06600'))
            client.get(URL.format(cp='06600'))
            client.get(URL.format(cp='06600'))
        # Solo una llamada al provider — las otras dos vienen del caché.
        assert mock.call_count == 1


# ── Tests de los clientes individuales (zippopotam + google) ────────────────

class TestCopomexClient:
    def test_parses_multiple_neighborhoods(self, settings):
        from apps.places.clients import fetch_from_copomex

        settings.COPOMEX_TOKEN = 'test-token'
        # Forma real del response de copomex: lista, una entrada por colonia.
        fake_response = [
            {
                'error': False,
                'response': {
                    'cp': '79034',
                    'asentamiento': 'Palo de Rosa',
                    'municipio': 'Ciudad Valles',
                    'estado': 'San Luis Potosí',
                    'ciudad': 'Ciudad Valles',
                    'pais': 'México',
                },
            },
            {
                'error': False,
                'response': {
                    'cp': '79034',
                    'asentamiento': 'Centro',
                    'municipio': 'Ciudad Valles',
                    'estado': 'San Luis Potosí',
                    'ciudad': 'Ciudad Valles',
                    'pais': 'México',
                },
            },
        ]
        with patch('apps.places.clients.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = fake_response
            info = fetch_from_copomex('79034')

        assert info is not None
        assert info.state == 'San Luis Potosí'
        assert info.city == 'Ciudad Valles'
        assert info.neighborhoods == ['Palo de Rosa', 'Centro']
        assert info.source == 'copomex'

    def test_no_token_returns_none(self, settings):
        from apps.places.clients import fetch_from_copomex

        settings.COPOMEX_TOKEN = ''
        # No debe llamar a la API si no hay token
        with patch('apps.places.clients.requests.get') as mock_get:
            result = fetch_from_copomex('79034')
        assert result is None
        mock_get.assert_not_called()

    def test_404_returns_none(self, settings):
        from apps.places.clients import fetch_from_copomex

        settings.COPOMEX_TOKEN = 'test-token'
        with patch('apps.places.clients.requests.get') as mock_get:
            mock_get.return_value.status_code = 404
            assert fetch_from_copomex('99999') is None

    def test_error_object_returns_none(self, settings):
        from apps.places.clients import fetch_from_copomex

        settings.COPOMEX_TOKEN = 'test-token'
        with patch('apps.places.clients.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'error': True, 'error_message': 'CP no existe',
            }
            assert fetch_from_copomex('99999') is None

    def test_5xx_raises_provider_error(self, settings):
        from apps.places.clients import fetch_from_copomex

        settings.COPOMEX_TOKEN = 'test-token'
        with patch('apps.places.clients.requests.get') as mock_get:
            mock_get.return_value.status_code = 502
            with pytest.raises(PostalCodeProviderError):
                fetch_from_copomex('79034')


class TestZippopotamClient:
    def test_parses_valid_response(self):
        from apps.places.clients import fetch_from_zippopotam

        fake_response = {
            'country': 'Mexico',
            'post code': '06600',
            'places': [{
                'place name': 'Juarez',
                'longitude': '-99.165',
                'latitude': '19.385',
                'state': 'Distrito Federal',
                'state abbreviation': 'DIF',
            }],
        }

        with patch('apps.places.clients.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = fake_response
            info = fetch_from_zippopotam('06600')

        assert info is not None
        # "Distrito Federal" debe normalizarse a "Ciudad de México"
        assert info.state == 'Ciudad de México'
        assert info.neighborhoods == ['Juarez']
        assert info.lat == 19.385
        assert info.source == 'zippopotam'

    def test_404_returns_none(self):
        from apps.places.clients import fetch_from_zippopotam

        with patch('apps.places.clients.requests.get') as mock_get:
            mock_get.return_value.status_code = 404
            result = fetch_from_zippopotam('99999')

        assert result is None

    def test_5xx_raises_provider_error(self):
        from apps.places.clients import fetch_from_zippopotam

        with patch('apps.places.clients.requests.get') as mock_get:
            mock_get.return_value.status_code = 503
            with pytest.raises(PostalCodeProviderError):
                fetch_from_zippopotam('06600')

    def test_network_error_raises_provider_error(self):
        import requests as requests_lib
        from apps.places.clients import fetch_from_zippopotam

        with patch('apps.places.clients.requests.get') as mock_get:
            mock_get.side_effect = requests_lib.ConnectionError('boom')
            with pytest.raises(PostalCodeProviderError):
                fetch_from_zippopotam('06600')


class TestGoogleClient:
    def test_parses_address_components(self, settings):
        from apps.places.clients import fetch_from_google

        settings.GOOGLE_PLACES_API_KEY = 'fake-key'
        fake_response = {
            'places': [{
                'formattedAddress': 'Juárez, 06600 CDMX',
                'location': {'latitude': 19.385, 'longitude': -99.165},
                'addressComponents': [
                    {'longText': '06600', 'types': ['postal_code']},
                    {'longText': 'Juárez', 'types': ['sublocality', 'sublocality_level_1']},
                    {'longText': 'Ciudad de México', 'types': ['locality']},
                    {'longText': 'Ciudad de México', 'types': ['administrative_area_level_1']},
                    {'longText': 'México', 'types': ['country']},
                ],
            }],
        }

        with patch('apps.places.clients.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = fake_response
            info = fetch_from_google('06600')

        assert info is not None
        assert info.state == 'Ciudad de México'
        assert info.city == 'Ciudad de México'
        assert 'Juárez' in info.neighborhoods
        assert info.source == 'google'

    def test_no_api_key_returns_none(self, settings):
        from apps.places.clients import fetch_from_google

        settings.GOOGLE_PLACES_API_KEY = ''
        result = fetch_from_google('06600')
        assert result is None

    def test_empty_places_returns_none(self, settings):
        from apps.places.clients import fetch_from_google

        settings.GOOGLE_PLACES_API_KEY = 'fake-key'
        with patch('apps.places.clients.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'places': []}
            assert fetch_from_google('99999') is None


class TestOrquestador:
    def test_copomex_success_skips_others(self):
        """Si copomex responde, no llamamos a los providers de fallback."""
        from apps.places.clients import lookup_postal_code

        info = PostalCodeInfo(
            postal_code='79034',
            state='San Luis Potosí',
            city='Ciudad Valles',
            neighborhoods=['Palo de Rosa', 'Centro'],
            source='copomex',
        )
        with patch('apps.places.clients.fetch_from_copomex', return_value=info) as c, \
             patch('apps.places.clients.fetch_from_zippopotam') as z, \
             patch('apps.places.clients.fetch_from_google') as g:
            result = lookup_postal_code('79034')
        assert result.source == 'copomex'
        assert 'Palo de Rosa' in result.neighborhoods
        c.assert_called_once()
        z.assert_not_called()
        g.assert_not_called()

    def test_copomex_none_falls_back_to_zippopotam(self):
        """Sin token de copomex (devuelve None), cae a zippopotam."""
        from apps.places.clients import lookup_postal_code

        zippo_info = PostalCodeInfo(
            postal_code='06600',
            state='Ciudad de México', city='Juarez',
            neighborhoods=['Juarez'], source='zippopotam',
        )
        with patch('apps.places.clients.fetch_from_copomex', return_value=None), \
             patch('apps.places.clients.fetch_from_zippopotam', return_value=zippo_info), \
             patch('apps.places.clients.fetch_from_google') as g:
            result = lookup_postal_code('06600')
        assert result.source == 'zippopotam'
        g.assert_not_called()

    def test_all_none_falls_back_to_google(self):
        from apps.places.clients import lookup_postal_code

        google_info = PostalCodeInfo(
            postal_code='06600',
            state='Ciudad de México', city='Ciudad de México',
            neighborhoods=['Juárez'], source='google',
        )
        with patch('apps.places.clients.fetch_from_copomex', return_value=None), \
             patch('apps.places.clients.fetch_from_zippopotam', return_value=None), \
             patch('apps.places.clients.fetch_from_google', return_value=google_info):
            result = lookup_postal_code('06600')
        assert result.source == 'google'

    def test_all_fail_raises_not_found(self):
        from apps.places.clients import lookup_postal_code

        with patch('apps.places.clients.fetch_from_copomex', return_value=None), \
             patch('apps.places.clients.fetch_from_zippopotam', return_value=None), \
             patch('apps.places.clients.fetch_from_google', return_value=None):
            with pytest.raises(PostalCodeNotFound):
                lookup_postal_code('99999')

    def test_all_technical_errors_raise_provider_error(self):
        """Si TODOS los providers fallan técnicamente, propagar como ProviderError."""
        from apps.places.clients import lookup_postal_code

        with patch('apps.places.clients.fetch_from_copomex',
                   side_effect=PostalCodeProviderError('copomex 503')), \
             patch('apps.places.clients.fetch_from_zippopotam',
                   side_effect=PostalCodeProviderError('zippopotam 503')), \
             patch('apps.places.clients.fetch_from_google',
                   side_effect=PostalCodeProviderError('google 500')):
            with pytest.raises(PostalCodeProviderError):
                lookup_postal_code('79034')

    def test_invalid_cp_format_raises_immediately(self):
        from apps.places.clients import lookup_postal_code

        with pytest.raises(PostalCodeNotFound):
            lookup_postal_code('abc')
        with pytest.raises(PostalCodeNotFound):
            lookup_postal_code('123')
