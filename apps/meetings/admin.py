from django.contrib import admin

from .models import Room, Meeting


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'capacity', 'is_active', 'tenant']
    list_filter = ['is_active', 'branch']
    search_fields = ['name']


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'start_time', 'end_time', 'organizer', 'room', 'tenant']
    list_filter = ['date']
    search_fields = ['title']
    filter_horizontal = ['participants']
