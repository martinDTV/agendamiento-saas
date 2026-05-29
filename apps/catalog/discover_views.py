"""
Endpoints de descubrimiento público (cross-clínica).

A diferencia de `PublicDoctorViewSet`/`PublicServiceViewSet` que solo devuelven
los catálogos del tenant actual (filtrado vía `X-Tenant-Slug`), estos endpoints
son **globales**: devuelven datos de TODAS las clínicas activas del SaaS.

Diseñados para la app móvil de pacientes, donde el paciente:
  1. Abre la app sin saber a qué clínica va.
  2. Ve doctores y clínicas disponibles.
  3. Elige uno, y al reservar el backend ya sabe a qué tenant pertenece.

Notas técnicas:
  - Usamos los managers `_all` (no scoped) para saltar el filtro por tenant.
  - Solo exponemos `is_active=True` para tanto Doctor como Tenant.
  - Cada doctor/servicio del response incluye `tenant_slug` y `tenant_name`
    para que la app móvil sepa dónde reservar.
"""
from rest_framework import serializers, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.tenants.models import Tenant

from .models import Doctor, Service


# ── Serializers públicos cross-clínica ───────────────────────────────────────

class DiscoverDoctorSerializer(serializers.ModelSerializer):
    """Doctor + datos mínimos del tenant al que pertenece."""
    full_name = serializers.SerializerMethodField()
    # tenant_id es UUIDField en el modelo (ver apps/tenants/models.py:11),
    # NO IntegerField. La app móvil lo trata como string.
    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    photo_url = serializers.SerializerMethodField()

    # Agregados de reseñas — vienen como annotations del queryset (ver
    # DiscoverDoctorsView.get_queryset). Si el doctor no tiene reviews,
    # avg_rating es None y review_count es 0.
    avg_rating = serializers.FloatField(read_only=True, allow_null=True)
    review_count = serializers.IntegerField(read_only=True)

    # Próxima disponibilidad — solo se calcula si la view pasa
    # `with_next_slot=True` en el contexto, porque correr el cálculo para CADA
    # doctor es costoso (N queries). El cliente lo activa con
    # ?with_next_slot=true.
    next_available = serializers.SerializerMethodField()

    # Distancia en km al usuario — solo presente si la request trae lat/lng.
    # La view la inyecta en el contexto como dict {doctor_id: km}.
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            'id',
            'full_name',
            'specialty',
            'bio',
            'photo_url',
            'appointment_duration',
            'tenant_id',
            'tenant_slug',
            'tenant_name',
            'avg_rating',
            'review_count',
            'next_available',
            'distance_km',
        ]

    def get_distance_km(self, obj):
        distances = self.context.get('distances') or {}
        return distances.get(str(obj.id))

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.email

    def get_next_available(self, obj):
        if not self.context.get('with_next_slot'):
            return None
        from apps.bookings.slots import get_next_available_slot
        return get_next_available_slot(obj)

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        # `obj.photo.url` es relativo (ej. "/media/doctors/foo.jpg"). Necesitamos
        # URL ABSOLUTA porque la app móvil corre en otro dispositivo (iPhone)
        # y "localhost" ahí significa el iPhone, no la Mac que sirve el backend.
        #
        # Prioridad:
        #   1. SITE_URL del settings (configurado con la IP de LAN en .env)
        #   2. request.build_absolute_uri si SITE_URL no está
        from django.conf import settings
        url = obj.photo.url
        site_url = getattr(settings, 'SITE_URL', None)
        if site_url:
            return f"{site_url.rstrip('/')}{url}"
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class DiscoverClinicSerializer(serializers.ModelSerializer):
    """Tenant + conteo de doctores activos para mostrar en la app."""
    id = serializers.UUIDField(read_only=True)
    doctor_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ['id', 'slug', 'name', 'doctor_count']

    def get_doctor_count(self, obj):
        # Inyectado por `prefetch_related` para evitar N+1.
        return getattr(obj, '_doctor_count', None) or Doctor._all.filter(
            tenant=obj, is_active=True,
        ).count()


# ── ViewSets ─────────────────────────────────────────────────────────────────

class DiscoverDoctorsView(viewsets.ReadOnlyModelViewSet):
    """
    GET /rest/v1/public/discover/doctors/

    Lista pública de TODOS los doctores activos del SaaS, sin filtrar por
    tenant. Cada item incluye `tenant_slug` / `tenant_name` para que la app
    móvil muestre el badge de clínica.

    Query params (opcionales):
      - tenant: filtra por slug de clínica específica
      - specialty: filtra por especialidad (icontains)
      - q: busca en nombre del doctor, email, especialidad
      - lat, lng: ubicación del usuario para ordenar por distancia.
        Requiere AMBOS o se ignora.
      - radius_km: si lat/lng vienen, filtra solo doctores dentro del radio.
        Default 50km.
      - with_next_slot: 'true' para calcular próxima disponibilidad (caro)
    """
    permission_classes = [AllowAny]
    serializer_class = DiscoverDoctorSerializer
    pagination_class = None

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # `?with_next_slot=true` activa el cálculo de próxima disponibilidad
        # por doctor. Por defecto NO se calcula porque es costoso (N queries).
        param = self.request.query_params.get('with_next_slot', '').lower()
        ctx['with_next_slot'] = param in ('true', '1', 'yes')
        return ctx

    def list(self, request, *args, **kwargs):
        """
        Override `list` para meter el cálculo de distancia DESPUÉS de la query
        SQL — Haversine no se puede expresar como una expresión Django ORM
        portable (sin PostGIS). Hacemos:
          1. qs filtrado por SQL (tenant/specialty/q)
          2. Para cada doctor con branch geocodificada, calcular distancia
          3. Filtrar por radius_km
          4. Ordenar por distancia ascendente
          5. Serializar (con `distance_km` inyectado al contexto por doctor)
        """
        from apps.places.geo import haversine_km, parse_latlng

        qs = self.filter_queryset(self.get_queryset())

        lat = parse_latlng(request.query_params.get('lat'))
        lng = parse_latlng(request.query_params.get('lng'))
        location_provided = lat is not None and lng is not None

        if not location_provided:
            # Sin ubicación — comportamiento normal
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)

        try:
            radius_km = float(request.query_params.get('radius_km', 50))
        except (TypeError, ValueError):
            radius_km = 50.0

        # Calcular distancia por doctor. Si la branch del doctor NO tiene
        # coordenadas, lo dejamos AL FINAL con distance=None (no se filtra
        # por radio, pero se ordena último).
        items: list[tuple[float | None, Doctor]] = []
        for doctor in qs:
            branch = getattr(doctor, 'branch', None)
            if branch and branch.address_lat and branch.address_lng:
                dist = haversine_km(
                    lat, lng, branch.address_lat, branch.address_lng,
                )
                if dist <= radius_km:
                    items.append((dist, doctor))
                # Si está fuera del radio, lo excluimos
            else:
                # Sin geocodificar — incluir solo si el usuario NO pidió
                # filtro estricto (radius_km > 0). En la práctica siempre
                # filtramos, así que estos quedan fuera.
                # Para ser amables, los incluimos al final.
                items.append((None, doctor))

        # Ordenar: primero los con distancia (ascending), luego los sin
        items.sort(key=lambda x: (x[0] is None, x[0] or 0))

        # Inyectar la distancia al contexto serializado por doctor
        ctx = self.get_serializer_context()
        ctx['distances'] = {str(doc.id): dist for dist, doc in items}
        serializer = self.get_serializer_class()(
            [doc for _, doc in items], many=True, context=ctx,
        )
        return Response(serializer.data)

    def get_queryset(self):
        from django.db.models import Avg, Count, Q

        qs = (
            Doctor._all
            .filter(is_active=True, tenant__is_active=True)
            .select_related('user', 'tenant', 'branch')
            # Anotamos rating promedio y conteo de reseñas publicadas.
            # `filter` dentro de Avg/Count limita a is_published=True.
            .annotate(
                avg_rating=Avg(
                    'reviews__rating',
                    filter=Q(reviews__is_published=True),
                ),
                review_count=Count(
                    'reviews',
                    filter=Q(reviews__is_published=True),
                ),
            )
            .order_by('tenant__name', 'user__first_name')
        )
        params = self.request.query_params
        if params.get('tenant'):
            qs = qs.filter(tenant__slug=params['tenant'].strip().lower())
        if params.get('specialty'):
            qs = qs.filter(specialty__icontains=params['specialty'])
        if params.get('q'):
            from django.db.models import Q
            q = params['q'].strip()
            qs = qs.filter(
                Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(user__email__icontains=q)
                | Q(specialty__icontains=q)
            )
        return qs


class DiscoverClinicsView(viewsets.ReadOnlyModelViewSet):
    """
    GET /rest/v1/public/discover/clinics/

    Lista pública de clínicas activas del SaaS. Cada item incluye el conteo
    de doctores activos para mostrar en la app.
    """
    permission_classes = [AllowAny]
    serializer_class = DiscoverClinicSerializer
    pagination_class = None

    def get_queryset(self):
        return Tenant.objects.filter(is_active=True).order_by('name')


class DiscoverServicesView(viewsets.ReadOnlyModelViewSet):
    """
    GET /rest/v1/public/discover/services/?doctor=<id>

    Lista los servicios que ofrece un doctor específico. Requiere `doctor` en
    query params — sin filtro por tenant porque ya sabemos qué doctor es.
    """
    permission_classes = [AllowAny]
    pagination_class = None

    def get_serializer_class(self):
        # Mismo formato que ServiceSerializer pero sin doctor_ids (no necesario aquí).
        class _S(serializers.ModelSerializer):
            class Meta:
                model = Service
                fields = ['id', 'name', 'description', 'duration', 'price']

        return _S

    def get_queryset(self):
        doctor_id = self.request.query_params.get('doctor')
        if not doctor_id:
            return Service._all.none()
        return (
            Service._all
            .filter(doctors__id=doctor_id, is_active=True, tenant__is_active=True)
            .distinct()
            .order_by('name')
        )
