from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsTenantAdminOrOwner
from apps.tenants.models import Tenant
from apps.tenants.serializers import TenantPublicSerializer, TenantAdminSerializer, TenantSelfSerializer


class TenantResolveView(viewsets.ViewSet):
    """
    Public endpoint used by Nuxt SSR to resolve the current tenant from its slug.

    GET /rest/v1/tenants/resolve/{slug}/
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'], url_path='resolve/(?P<slug>[\\w-]+)')
    def resolve(self, request, slug=None):
        tenant = Tenant.objects.filter(slug=slug, is_active=True).first()
        if tenant is None:
            # In demo mode, the SSR resolve call is the first hit for a clinic
            # (the Host is the apex, so the middleware can't auto-create). Create
            # + seed the demo tenant here so the clinic comes alive on first load.
            from apps.tenants.middleware import get_or_create_demo_tenant
            tenant = get_or_create_demo_tenant(slug)
        if tenant is None:
            from django.http import Http404
            raise Http404('No Tenant matches the given query.')
        serializer = TenantPublicSerializer(tenant)
        return Response(serializer.data)


class TenantSelfView(APIView):
    """
    GET/PATCH /rest/v1/tenants/me/

    Returns or updates the current request's tenant.
    Requires authenticated admin/owner.
    """
    permission_classes = [IsAuthenticated, IsTenantAdminOrOwner]

    def get(self, request):
        serializer = TenantSelfSerializer(request.tenant)
        return Response(serializer.data)

    def patch(self, request):
        serializer = TenantSelfSerializer(request.tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TenantViewSet(viewsets.ModelViewSet):
    """
    Platform-admin CRUD for tenants. Requires superuser.
    """
    permission_classes = [IsAdminUser]
    serializer_class = TenantAdminSerializer
    queryset = Tenant.objects.all()
    lookup_field = 'slug'
