"""Serializers de reseñas — caminos autenticado y anónimo."""
from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import Doctor
from apps.patients.models import Patient

from .models import PendingReview, Review


class ReviewSerializer(serializers.ModelSerializer):
    """Output de reseñas publicadas — usado por GET endpoints."""
    author_name = serializers.CharField(source='author_display_name', read_only=True)
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'doctor', 'doctor_name',
            'author_name',
            'appointment', 'rating', 'comment',
            'is_published', 'created_at', 'updated_at',
        ]
        read_only_fields = fields  # output-only

    def get_doctor_name(self, obj):
        return str(obj.doctor)


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    POST /rest/v1/reviews/ (requiere auth).

    El `patient` se infiere del request.user. Se publica inmediatamente
    porque hay identidad verificada (cuenta + email confirmado).
    """
    class Meta:
        model = Review
        fields = ['doctor', 'appointment', 'rating', 'comment']

    def validate_doctor(self, value):
        if not isinstance(value, Doctor):
            raise serializers.ValidationError('Doctor inválido.')
        return value

    def validate(self, data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError('Requiere autenticación.')

        patient = Patient.objects.filter(user=request.user).first()
        if not patient:
            raise serializers.ValidationError(
                'Este usuario no tiene perfil de paciente.'
            )

        # Verifica que no exista ya una reseña (en update se omite)
        if not self.instance:
            exists = Review.objects.filter(
                patient=patient, doctor=data['doctor'],
            ).exists()
            if exists:
                raise serializers.ValidationError(
                    'Ya escribiste una reseña para este doctor. Edita la existente.'
                )

        data['patient'] = patient
        # Copiamos nombre + email para que `author_display_name` funcione
        # también cuando el patient se borra/anonimiza después.
        data['reviewer_name'] = patient.full_name
        data['reviewer_email'] = patient.email
        return data

    def create(self, validated_data):
        return Review.objects.create(**validated_data)


class AnonymousReviewCreateSerializer(serializers.ModelSerializer):
    """
    POST /rest/v1/public/reviews/ (sin auth).

    Crea un `PendingReview` y manda email con link de confirmación.
    NO se publica hasta que el usuario confirma su email.
    """
    class Meta:
        model = PendingReview
        fields = [
            'doctor', 'reviewer_name', 'reviewer_email',
            'rating', 'comment',
        ]

    def validate_doctor(self, value):
        if not isinstance(value, Doctor):
            raise serializers.ValidationError('Doctor inválido.')
        if not value.is_active:
            raise serializers.ValidationError('Doctor no disponible.')
        return value

    def validate_reviewer_email(self, value):
        return value.strip().lower()

    def validate_reviewer_name(self, value):
        name = value.strip()
        if len(name) < 2:
            raise serializers.ValidationError('Nombre demasiado corto.')
        return name

    def validate(self, data):
        # Si ya existe una Review publicada de este email para este doctor,
        # rechazamos para evitar duplicados.
        exists = Review.objects.filter(
            doctor=data['doctor'],
            reviewer_email__iexact=data['reviewer_email'],
            is_published=True,
        ).exists()
        if exists:
            raise serializers.ValidationError(
                'Ya tienes una reseña publicada para este doctor con este correo.'
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        # Si ya hay un PendingReview NO confirmado del mismo email+doctor,
        # lo borramos antes (re-envío de link).
        PendingReview.objects.filter(
            doctor=validated_data['doctor'],
            reviewer_email__iexact=validated_data['reviewer_email'],
            confirmed_at__isnull=True,
        ).delete()
        return PendingReview.objects.create(**validated_data)


class ConfirmReviewSerializer(serializers.Serializer):
    """Confirma una reseña pendiente con su token UUID."""
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            pending = PendingReview.objects.select_related('doctor').get(token=value)
        except PendingReview.DoesNotExist:
            raise serializers.ValidationError('Token inválido.')
        if pending.is_confirmed:
            raise serializers.ValidationError('Esta reseña ya fue confirmada.')
        if pending.is_expired:
            raise serializers.ValidationError('Este link ha expirado.')
        self.context['pending'] = pending
        return value

    @transaction.atomic
    def save(self):
        from django.utils import timezone
        pending: PendingReview = self.context['pending']

        # Si ya hay una Review publicada para este (email, doctor), no
        # creamos otra — preservamos la integridad del rating.
        existing = Review.objects.filter(
            doctor=pending.doctor,
            reviewer_email__iexact=pending.reviewer_email,
            is_published=True,
        ).first()

        if existing:
            review = existing
        else:
            review = Review.objects.create(
                doctor=pending.doctor,
                patient=None,
                reviewer_name=pending.reviewer_name,
                reviewer_email=pending.reviewer_email,
                rating=pending.rating,
                comment=pending.comment,
                is_published=True,
            )

        pending.confirmed_at = timezone.now()
        pending.confirmed_review = review
        pending.save(update_fields=['confirmed_at', 'confirmed_review'])
        return review
