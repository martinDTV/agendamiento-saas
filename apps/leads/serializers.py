from rest_framework import serializers

from .models import Lead


class LeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'plan', 'message', 'source']
        extra_kwargs = {
            'phone': {'required': False},
            'plan': {'required': False},
            'message': {'required': False},
            'source': {'required': False},
        }

    def validate_name(self, value):
        value = (value or '').strip()
        if len(value) < 2:
            raise serializers.ValidationError('Ingresa tu nombre.')
        return value
