from django.contrib import admin
from .models import Plan, Subscription, Discount


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price_monthly', 'price_yearly', 'is_active', 'sort_order')
    list_filter = ('is_active', 'is_public')
    search_fields = ('name', 'slug')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'plan', 'status', 'billing_cycle', 'current_period_end')
    list_filter = ('status', 'billing_cycle', 'plan')
    search_fields = ('tenant__name', 'tenant__slug')


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'is_active', 'times_used')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'description')
