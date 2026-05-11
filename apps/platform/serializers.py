from rest_framework import serializers

from apps.tenants.models import Tenant

from .models import Plan, Subscription, Discount, PlatformSettings


class PlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformSettings
        fields = ['primary_color', 'platform_name', 'support_email', 'logo_url', 'updated_at']
        read_only_fields = ['updated_at']


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'slug', 'description',
            'price_monthly', 'price_yearly', 'currency',
            'max_doctors', 'max_appointments_per_month', 'max_branches',
            'features', 'flags',
            'paypal_product_id', 'paypal_plan_id',
            'is_active', 'is_public', 'sort_order',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'paypal_plan_id']


class DiscountSerializer(serializers.ModelSerializer):
    applicable_plan_names = serializers.SerializerMethodField()

    class Meta:
        model = Discount
        fields = [
            'id', 'code', 'description',
            'discount_type', 'value',
            'applicable_plans', 'applicable_plan_names',
            'valid_from', 'valid_until',
            'max_uses', 'times_used',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'times_used', 'created_at', 'applicable_plan_names']

    def get_applicable_plan_names(self, obj):
        return [p.name for p in obj.applicable_plans.all()]


class SubscriptionSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_price_monthly = serializers.DecimalField(
        source='plan.price_monthly', max_digits=10, decimal_places=2, read_only=True,
    )
    discount_code = serializers.CharField(source='discount.code', read_only=True, default=None)

    class Meta:
        model = Subscription
        fields = [
            'id',
            'tenant', 'tenant_name', 'tenant_slug',
            'plan', 'plan_name', 'plan_price_monthly',
            'status', 'billing_cycle',
            'discount', 'discount_code',
            'started_at', 'current_period_end', 'canceled_at', 'trial_ends_at',
            'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'tenant_name', 'tenant_slug',
            'plan_name', 'plan_price_monthly', 'discount_code',
            'created_at', 'updated_at',
        ]


class TenantPlatformSerializer(serializers.ModelSerializer):
    """Serializer enriquecido del Tenant para el panel de plataforma."""

    subscription = SubscriptionSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    plan_display = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'slug', 'name', 'type', 'plan', 'plan_display',
            'custom_domain', 'is_active', 'created_at',
            'settings', 'subscription', 'member_count',
        ]
        read_only_fields = ['id', 'created_at', 'subscription', 'member_count', 'plan_display']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # slug es asignable al crear pero immutable al actualizar:
        # cambiarlo rompe URLs activas, correos de confirmación y sesiones.
        if self.instance is not None:
            self.fields['slug'].read_only = True

    def get_member_count(self, obj):
        return obj.accounts_membership_set.filter(is_active=True).count()

    def get_plan_display(self, obj):
        """
        Resuelve el nombre legible del plan:
        1. Si hay Subscription → nombre del plan suscrito
        2. Si no, busca por slug en la tabla Plan
        3. Fallback al slug capitalizado
        """
        sub = getattr(obj, 'subscription', None)
        if sub and sub.plan:
            return sub.plan.name
        if obj.plan:
            plan = Plan.objects.filter(slug=obj.plan).first()
            if plan:
                return plan.name
            return obj.plan.capitalize()
        return None
