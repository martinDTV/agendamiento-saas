from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'rating', 'is_published', 'created_at']
    list_filter = ['rating', 'is_published', 'created_at']
    search_fields = ['patient__user__email', 'doctor__user__email', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['patient', 'doctor', 'appointment']
