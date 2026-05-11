from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import Membership, InvitationToken, MembershipRole
from apps.tenants.models import Tenant
from apps.tenants.serializers import TenantPublicSerializer

User = get_user_model()


class MembershipSerializer(serializers.ModelSerializer):
    user            = serializers.IntegerField(source='user.id', read_only=True)
    user_email      = serializers.EmailField(source='user.email', read_only=True)
    user_uuid       = serializers.UUIDField(source='user.uuid', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name  = serializers.CharField(source='user.last_name', read_only=True)
    user_full_name  = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = [
            'id', 'user', 'user_email', 'user_uuid',
            'user_first_name', 'user_last_name', 'user_full_name',
            'role', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.email


class TenantRegistrationSerializer(serializers.Serializer):
    # Tenant fields
    tenant_name = serializers.CharField(max_length=255)
    tenant_slug = serializers.SlugField(max_length=63)
    tenant_type = serializers.ChoiceField(choices=['solo', 'clinic'], default='solo')

    # Owner fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=150, required=False, default='')
    last_name = serializers.CharField(max_length=150, required=False, default='')

    def validate_tenant_slug(self, value):
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError('Este slug ya está en uso.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Ya existe una cuenta con este email.')
        return value


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[r for r in MembershipRole.values if r != MembershipRole.OWNER]
    )

    def validate_email(self, value):
        tenant = self.context['tenant']
        if Membership.objects.for_tenant(tenant).filter(user__email=value, is_active=True).exists():
            raise serializers.ValidationError('Este usuario ya es miembro del tenant.')
        return value


class InvitationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvitationToken
        fields = ['id', 'email', 'role', 'token', 'expires_at', 'accepted_at', 'created_at']
        read_only_fields = fields


class MeSerializer(serializers.ModelSerializer):
    memberships = serializers.SerializerMethodField()
    uuid = serializers.UUIDField(read_only=True)
    must_change_password = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'uuid', 'email', 'first_name', 'last_name', 'is_superuser', 'memberships', 'must_change_password', 'profile_picture_url']

    def get_profile_picture_url(self, user):
        profile = getattr(user, 'profile', None)
        if not profile or not profile.profile_picture:
            return None
        request = self.context.get('request')
        url = profile.profile_picture.url
        return request.build_absolute_uri(url) if request else url

    def get_memberships(self, user):
        memberships = Membership._all.filter(user=user, is_active=True).select_related('tenant')
        return [
            {
                'tenant_slug': m.tenant.slug,
                'tenant_name': m.tenant.name,
                'role': m.role,
            }
            for m in memberships
        ]

    def get_must_change_password(self, user):
        return hasattr(user, 'password_change_required')
