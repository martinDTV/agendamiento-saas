import uuid
from django.db import models


class TenantType(models.TextChoices):
    SOLO = 'solo', 'Doctor independiente'
    CLINIC = 'clinic', 'Clínica'


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, max_length=63, db_index=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TenantType.choices, default=TenantType.SOLO)
    plan = models.CharField(max_length=50, default='free')
    custom_domain = models.CharField(max_length=255, blank=True, null=True, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    settings = models.JSONField(
        default=dict,
        help_text='Branding, timezone, locale, and feature flags per tenant.',
    )

    class Meta:
        db_table = 'tenants'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.slug})'

    @property
    def public_url(self):
        from django.conf import settings as django_settings
        domain = django_settings.PLATFORM_DOMAIN
        return f'https://{self.slug}.{domain}'

    @property
    def admin_url(self):
        from django.conf import settings as django_settings
        domain = django_settings.PLATFORM_DOMAIN
        return f'https://admin.{self.slug}.{domain}'
