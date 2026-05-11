from datetime import timedelta

from django.utils import timezone

from rest_framework import serializers
from apps.tenants.models import Tenant


def _sync_subscription_with_plan(tenant: Tenant) -> None:
    """
    Mantiene `Subscription` alineada con `Tenant.plan`. Llamar después de que
    `Tenant.plan` cambie (o al crear un tenant) para crear/actualizar la fila
    de Subscription correspondiente. Silencioso si la tabla Plan no tiene el slug.
    """
    # Imports locales para evitar ciclos en tiempo de carga.
    from apps.platform.models import Plan, Subscription

    plan = Plan.objects.filter(slug=tenant.plan).first()
    if plan is None:
        plan = Plan.objects.filter(slug='free').first()
    if plan is None:
        return

    today = timezone.now().date()
    is_free = plan.price_monthly == 0
    defaults = {
        'plan': plan,
        'status': 'active' if is_free else 'trial',
        'billing_cycle': 'monthly',
        'started_at': today,
        'current_period_end': today + (timedelta(days=365 * 10) if is_free else timedelta(days=30)),
        'trial_ends_at': None if is_free else today + timedelta(days=14),
    }

    sub, created = Subscription.objects.get_or_create(tenant=tenant, defaults=defaults)
    if not created and sub.plan_id != plan.id:
        sub.plan = plan
        if is_free:
            sub.status = 'active'
            sub.trial_ends_at = None
            sub.current_period_end = today + timedelta(days=365 * 10)
        sub.save(update_fields=['plan', 'status', 'trial_ends_at', 'current_period_end', 'updated_at'])


class TenantPublicSerializer(serializers.ModelSerializer):
    """Minimal tenant data safe to expose publicly (used by Nuxt SSR for tenant resolution)."""

    plan_flags = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ['id', 'slug', 'name', 'type', 'plan', 'plan_flags', 'settings']
        read_only_fields = fields

    def get_plan_flags(self, obj):
        """
        Subset de flags que el sitio público necesita conocer (white-label, etc).
        No exponemos flags privados (api_access, sso_saml, etc).
        """
        from apps.platform.feature_flags import tenant_has_feature
        return {
            'white_label': tenant_has_feature(obj, 'white_label'),
            'cms_editor': tenant_has_feature(obj, 'cms_editor'),
            'ai_booking_suggestions': tenant_has_feature(obj, 'ai_booking_suggestions'),
            'chat_human_support': tenant_has_feature(obj, 'chat_human_support'),
            'chat_ai_support': tenant_has_feature(obj, 'chat_ai_support'),
        }


class TenantAdminSerializer(serializers.ModelSerializer):
    """Full tenant data for platform admins only."""

    class Meta:
        model = Tenant
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def update(self, instance, validated_data):
        old_plan = instance.plan
        tenant = super().update(instance, validated_data)
        if tenant.plan != old_plan:
            _sync_subscription_with_plan(tenant)
        return tenant

    def create(self, validated_data):
        tenant = super().create(validated_data)
        _sync_subscription_with_plan(tenant)
        return tenant


class TenantSelfSerializer(serializers.ModelSerializer):
    """Tenant members can update name and settings (branding, etc.)."""

    subscription = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ['id', 'slug', 'name', 'type', 'plan', 'settings', 'subscription', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at', 'plan', 'subscription']  # plan se cambia vía PayPal flow, no PATCH directo

    def get_subscription(self, obj):
        sub = getattr(obj, 'subscription', None)
        if not sub:
            return None
        return {
            'status': sub.status,
            'plan_slug': sub.plan.slug if sub.plan_id else None,
            'plan_name': sub.plan.name if sub.plan_id else None,
            'billing_cycle': sub.billing_cycle,
            'started_at': sub.started_at.isoformat() if sub.started_at else None,
            'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
            'trial_ends_at': sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
            'paypal_subscription_id': sub.paypal_subscription_id,
        }

    def validate_settings(self, value):
        """
        Gate de CMS: si el tenant intenta guardar `settings.content` y su plan
        no incluye `cms_editor`, lo rechazamos. El branding (color, logo) sigue
        editable para todos los planes.
        """
        from apps.platform.feature_flags import tenant_has_feature

        if not isinstance(value, dict):
            return value

        old_settings = (self.instance.settings if self.instance else {}) or {}
        new_content = value.get('content')
        old_content = old_settings.get('content')

        if new_content != old_content and not tenant_has_feature(self.instance, 'cms_editor'):
            raise serializers.ValidationError({
                'content': 'El editor de contenido no está incluido en tu plan. Actualiza a Starter o superior.'
            })
        return value

    def update(self, instance, validated_data):
        old_plan = instance.plan
        tenant = super().update(instance, validated_data)
        if tenant.plan != old_plan:
            _sync_subscription_with_plan(tenant)
        return tenant
