from django.db import models
from django.utils import timezone


class PlatformSettings(models.Model):
    """
    Configuración global del panel de plataforma (super admin).
    Singleton: siempre existe una sola fila (pk=1).

    Estos valores aplican EXCLUSIVAMENTE al panel del super admin
    (puerto 3004) y no se cruzan con el branding de los tenants.
    """

    primary_color = models.CharField(max_length=9, default='#6366f1', help_text='Color principal del panel (#RRGGBB)')
    platform_name = models.CharField(max_length=100, default='Plataforma')
    support_email = models.EmailField(blank=True, default='')
    logo_url = models.URLField(blank=True, default='')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'platform_settings'
        verbose_name = 'Ajustes de plataforma'
        verbose_name_plural = 'Ajustes de plataforma'

    def __str__(self):
        return self.platform_name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class Plan(models.Model):
    """Plan de suscripción ofrecido por la plataforma (ej. Free, Starter, Pro, Enterprise)."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=50)
    description = models.TextField(blank=True)

    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='MXN')

    max_doctors = models.IntegerField(default=1, help_text='0 = ilimitado')
    max_appointments_per_month = models.IntegerField(default=0, help_text='0 = ilimitado')
    max_branches = models.IntegerField(default=1, help_text='0 = ilimitado')

    features = models.JSONField(default=list, blank=True, help_text='Lista de features incluidas (texto, para mostrar en UI)')
    flags = models.JSONField(default=dict, blank=True, help_text='Feature flags booleanos. Schema en apps.platform.feature_flags.DEFAULT_FLAGS')

    # PayPal — IDs de los recursos sincronizados en PayPal
    paypal_product_id = models.CharField(max_length=64, blank=True, default='')
    paypal_plan_id = models.CharField(max_length=64, blank=True, default='', db_index=True)

    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True, help_text='Si aparece en la página de marketing')
    sort_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'platform_plans'
        ordering = ['sort_order', 'price_monthly']
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'

    def __str__(self):
        return f'{self.name} (${self.price_monthly}/mes)'


class SubscriptionStatus(models.TextChoices):
    TRIAL = 'trial', 'Periodo de prueba'
    ACTIVE = 'active', 'Activa'
    PAST_DUE = 'past_due', 'Pago vencido'
    CANCELED = 'canceled', 'Cancelada'
    SUSPENDED = 'suspended', 'Suspendida'


class BillingCycle(models.TextChoices):
    MONTHLY = 'monthly', 'Mensual'
    YEARLY = 'yearly', 'Anual'


class Subscription(models.Model):
    """Suscripción activa de un tenant a un plan."""

    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='subscription',
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')

    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
    )
    billing_cycle = models.CharField(
        max_length=10,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )

    discount = models.ForeignKey(
        'Discount',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subscriptions',
    )

    started_at = models.DateField(default=timezone.now)
    current_period_end = models.DateField()
    canceled_at = models.DateField(null=True, blank=True)
    trial_ends_at = models.DateField(null=True, blank=True)

    # PayPal integration
    paypal_subscription_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    paypal_plan_id = models.CharField(max_length=64, blank=True, default='')

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'platform_subscriptions'
        ordering = ['-created_at']
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'

    def __str__(self):
        return f'{self.tenant.name} → {self.plan.name} ({self.status})'


class DiscountType(models.TextChoices):
    PERCENT = 'percent', 'Porcentaje'
    FIXED = 'fixed', 'Monto fijo'


class Discount(models.Model):
    """Código de descuento aplicable a una suscripción."""

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)

    discount_type = models.CharField(max_length=10, choices=DiscountType.choices)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    applicable_plans = models.ManyToManyField(
        Plan,
        blank=True,
        related_name='discounts',
        help_text='Vacío = aplica a todos los planes',
    )

    valid_from = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)

    max_uses = models.IntegerField(null=True, blank=True, help_text='Vacío = ilimitado')
    times_used = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'platform_discounts'
        ordering = ['-created_at']
        verbose_name = 'Descuento'
        verbose_name_plural = 'Descuentos'

    def __str__(self):
        return f'{self.code} ({self.value}{"%" if self.discount_type == "percent" else " " + "MXN"})'


class PaymentEventType(models.TextChoices):
    SUBSCRIPTION_CREATED = 'subscription_created', 'Suscripción creada'
    SUBSCRIPTION_ACTIVATED = 'subscription_activated', 'Suscripción activada'
    SUBSCRIPTION_CANCELLED = 'subscription_cancelled', 'Suscripción cancelada'
    SUBSCRIPTION_SUSPENDED = 'subscription_suspended', 'Suscripción suspendida'
    PAYMENT_COMPLETED = 'payment_completed', 'Pago cobrado'
    PAYMENT_FAILED = 'payment_failed', 'Pago fallido'
    OTHER = 'other', 'Otro'


class PaymentTransaction(models.Model):
    """
    Log de eventos de pago. Cada llamada a PayPal o webhook recibido genera
    un registro. No es la fuente de verdad del status (eso vive en Subscription),
    es solo trazabilidad para auditoría / debug.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='payment_transactions',
    )
    subscription = models.ForeignKey(
        Subscription,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='transactions',
    )
    plan = models.ForeignKey(
        Plan,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='transactions',
    )

    event_type = models.CharField(max_length=40, choices=PaymentEventType.choices)
    provider = models.CharField(max_length=20, default='paypal')
    provider_event_id = models.CharField(max_length=64, blank=True, default='', db_index=True)
    provider_subscription_id = models.CharField(max_length=64, blank=True, default='', db_index=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True, default='')

    payload = models.JSONField(default=dict, blank=True, help_text='Cuerpo crudo del evento o respuesta')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'platform_payment_transactions'
        ordering = ['-created_at']
        verbose_name = 'Transacción de pago'
        verbose_name_plural = 'Transacciones de pago'

    def __str__(self):
        return f'{self.tenant.slug if self.tenant_id else "?"} · {self.event_type} · {self.created_at:%Y-%m-%d %H:%M}'
