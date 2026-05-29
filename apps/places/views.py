"""Endpoints públicos para autocomplete de direcciones."""
import hashlib
import re

from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .clients import (
    PostalCodeNotFound,
    PostalCodeProviderError,
    geocode_address,
    lookup_postal_code,
)


class PostalCodeThrottle(AnonRateThrottle):
    """
    Throttle conservador — el endpoint llama a Google Places que cuesta dinero.
    60 requests/min por IP es más que suficiente para uso legítimo (un paciente
    edita su CP ~1 vez), y bloquea scrapers básicos.
    """
    rate = '60/min'
    scope = 'postal_code'


CP_REGEX = re.compile(r'^\d{5}$')
# Caché 30 días — los CPs no cambian. Si Google cambia datos en su lado, el
# usuario verá la versión vieja por 30 días, lo cual es aceptable.
CACHE_TTL_SECONDS = 60 * 60 * 24 * 30


class PostalCodeLookupView(APIView):
    """
    GET /rest/v1/public/places/postal-code/{cp}/

    Devuelve estado, ciudad y colonias para un código postal mexicano.

    Sin auth (lo usa el formulario de registro/perfil). Throttle por IP.

    Response 200:
      {
        "postal_code": "06600",
        "state":       "Ciudad de México",
        "city":        "Ciudad de México",
        "neighborhoods": ["Juárez"],
        "country":     "México",
        "lat":         19.385,
        "lng":         -99.165,
        "source":      "zippopotam"
      }

    Response 404 si el CP no existe en ningún provider.
    Response 400 si el CP no tiene formato válido (5 dígitos).
    """
    permission_classes = [AllowAny]
    throttle_classes = [PostalCodeThrottle]

    def get(self, request, cp: str):
        if not CP_REGEX.match(cp):
            return Response(
                {'detail': 'Código postal inválido. Debe tener 5 dígitos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache_key = f'cp:{cp}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        try:
            info = lookup_postal_code(cp)
        except PostalCodeNotFound:
            return Response(
                {'detail': f'No encontramos información para el CP {cp}.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PostalCodeProviderError:
            # Si ambos providers fallan, devolvemos 503 (servicio dependiente
            # caído). El frontend debe permitir al usuario seguir llenando
            # manualmente.
            return Response(
                {'detail': 'El servicio de direcciones no está disponible. Llena los campos manualmente.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        data = info.to_dict()
        cache.set(cache_key, data, CACHE_TTL_SECONDS)
        return Response(data)


class GeocodeAddressThrottle(AnonRateThrottle):
    """Geocoding cuesta dinero — throttle más estricto que CP lookup."""
    rate = '30/min'
    scope = 'geocode'


class BranchLocationView(APIView):
    """
    GET /rest/v1/public/places/branch/{branch_id}/location/

    Devuelve lat/lng de una Branch. Si no tiene geocodificada, la geocodifica
    on-demand usando Google Places y guarda el resultado para la próxima vez.

    Response 200:
      {"lat": 19.43, "lng": -99.16, "formatted_address": "...", "source": "cache" | "google"}

    Response 404 si la branch no existe.
    Response 503 si no se pudo geocodificar (Google caído, address vacía).
    """
    permission_classes = [AllowAny]
    throttle_classes = [GeocodeAddressThrottle]

    def get(self, request, branch_id):
        from apps.catalog.models import Branch

        branch = Branch._all.filter(pk=branch_id, is_active=True).first()
        if not branch:
            return Response(
                {'detail': 'Sucursal no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Si ya está geocodificada, devolvemos de la BD
        if branch.address_lat is not None and branch.address_lng is not None:
            return Response({
                'lat': branch.address_lat,
                'lng': branch.address_lng,
                'formatted_address': branch.address,
                'source': 'cache',
            })

        # Si no, geocodificar on-demand
        if not branch.address.strip():
            return Response(
                {'detail': 'La sucursal no tiene dirección registrada.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Caché por dirección para no llamar a Google si dos branches tienen
        # la misma dirección (raro pero posible).
        cache_key = f'geocode:{hashlib.sha1(branch.address.encode()).hexdigest()}'
        cached = cache.get(cache_key)
        if cached:
            result_dict = cached
        else:
            result = geocode_address(branch.address)
            if not result:
                return Response(
                    {'detail': 'No se pudo geocodificar la dirección.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            result_dict = {
                'lat': result.lat,
                'lng': result.lng,
                'formatted_address': result.formatted_address,
                'source': result.source,
            }
            cache.set(cache_key, result_dict, 60 * 60 * 24 * 90)  # 90 días

        # Guardar en la branch para próximas requests (skip-write si fallaron)
        branch.address_lat = result_dict['lat']
        branch.address_lng = result_dict['lng']
        branch.address_geocoded_at = timezone.now()
        branch.save(update_fields=[
            'address_lat', 'address_lng', 'address_geocoded_at',
        ])

        return Response(result_dict)
