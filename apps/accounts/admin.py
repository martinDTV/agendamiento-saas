from django.contrib import admin
from apps.accounts.models import Membership, InvitationToken


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['user__email', 'tenant__slug']
    readonly_fields = ['id', 'created_at']


@admin.register(InvitationToken)
class InvitationTokenAdmin(admin.ModelAdmin):
    list_display = ['email', 'tenant', 'role', 'accepted_at', 'expires_at', 'created_at']
    list_filter = ['role']
    search_fields = ['email', 'tenant__slug']
    readonly_fields = ['id', 'token', 'created_at']
