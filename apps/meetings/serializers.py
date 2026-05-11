from rest_framework import serializers

from .models import Room, Meeting


class RoomSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'name', 'branch', 'branch_name', 'capacity', 'is_active', 'created_at']
        read_only_fields = ['id', 'branch_name', 'created_at']


class _MeetingUserMini(serializers.Serializer):
    """Mini user representation for participants_detail."""
    id            = serializers.IntegerField()
    email         = serializers.EmailField()
    full_name     = serializers.SerializerMethodField()

    def get_full_name(self, u):
        return u.get_full_name() or u.email


class MeetingSerializer(serializers.ModelSerializer):
    organizer_name      = serializers.SerializerMethodField()
    room_name           = serializers.CharField(source='room.name', read_only=True)
    participants_detail = _MeetingUserMini(source='participants', many=True, read_only=True)

    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'description',
            'organizer', 'organizer_name',
            'participants', 'participants_detail',
            'room', 'room_name',
            'date', 'start_time', 'end_time',
            'created_at',
        ]
        read_only_fields = ['id', 'organizer_name', 'room_name', 'participants_detail', 'created_at']

    def get_organizer_name(self, obj):
        return obj.organizer.get_full_name() or obj.organizer.email
