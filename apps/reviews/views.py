"""Endpoints de reseñas."""
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .emails import send_review_confirmation_email
from .models import Review
from .serializers import (
    AnonymousReviewCreateSerializer,
    ConfirmReviewSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
)


class DoctorReviewsView(APIView):
    """
    GET /rest/v1/public/reviews/doctor/{doctor_id}/

    Lista reseñas publicadas de un doctor. Pública (cualquiera puede ver
    rating de un doctor antes de reservar).
    """
    permission_classes = [AllowAny]

    def get(self, request, doctor_id):
        qs = (
            Review.objects.filter(doctor_id=doctor_id, is_published=True)
            .select_related('patient__user', 'doctor__user')
            .order_by('-created_at')[:50]
        )
        return Response(ReviewSerializer(qs, many=True).data)


class CreateReviewView(APIView):
    """
    POST /rest/v1/reviews/

    El paciente autenticado deja reseña a un doctor. Body:
      {"doctor": "<uuid>", "rating": 5, "comment": "...", "appointment": "<uuid>"}

    Se publica inmediatamente porque el patient tiene cuenta verificada.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class AnonymousReviewThrottle(AnonRateThrottle):
    """Throttle estricto contra spam de reseñas anónimas."""
    rate = '10/hour'
    scope = 'anonymous_review'


class CreateAnonymousReviewView(APIView):
    """
    POST /rest/v1/public/reviews/

    Crea una reseña ANÓNIMA. NO se publica de inmediato — se crea un
    PendingReview con token y se manda email al `reviewer_email`. Cuando
    el usuario hace click en el link del correo, se publica.

    Body:
      {
        "doctor": "<uuid>",
        "reviewer_name": "Juan Pérez",
        "reviewer_email": "juan@correo.com",
        "rating": 5,
        "comment": "Excelente atención"
      }

    Response 201:
      {"status": "pending", "message": "Revisa tu correo para confirmar..."}
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnonymousReviewThrottle]

    def post(self, request):
        serializer = AnonymousReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pending = serializer.save()
        send_review_confirmation_email(pending)
        return Response({
            'status': 'pending',
            'message': 'Revisa tu correo para confirmar tu reseña. El link expira en 7 días.',
            'email': pending.reviewer_email,
        }, status=status.HTTP_201_CREATED)


class ConfirmReviewView(APIView):
    """
    POST /rest/v1/public/reviews/confirm/   (cuerpo: {token})
    GET  /rest/v1/public/reviews/confirm/?token=...   (link del correo)

    Confirma una reseña pendiente y la publica. GET devuelve HTML porque
    es lo que abren los navegadores; POST devuelve JSON para apps.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConfirmReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response({
            'status': 'confirmed',
            'review_id': str(review.id),
        })

    def get(self, request):
        token = request.query_params.get('token', '').strip()
        if not token:
            return render(
                request, 'reviews/confirm_error.html',
                {'message': 'Falta el token de confirmación en el enlace.'},
                status=400,
            )

        serializer = ConfirmReviewSerializer(data={'token': token})
        if not serializer.is_valid():
            errors = serializer.errors
            msg = 'Enlace inválido.'
            if 'token' in errors and errors['token']:
                msg = str(errors['token'][0])
            return render(
                request, 'reviews/confirm_error.html',
                {'message': msg}, status=400,
            )

        review = serializer.save()
        return render(
            request, 'reviews/confirm_success.html',
            {
                'doctor_name': str(review.doctor),
                'rating': review.rating,
            },
            status=200,
        )
