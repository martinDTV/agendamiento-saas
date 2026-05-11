from django.contrib import admin
from apps.tenants.models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'type', 'plan', 'is_active', 'created_at']
    list_filter = ['type', 'plan', 'is_active']
    search_fields = ['name', 'slug', 'custom_domain']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    prepopulated_fields = {'slug': ('name',)}
