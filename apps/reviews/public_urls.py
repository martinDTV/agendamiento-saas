"""URLs públicas de reviews (sin auth)."""
from django.urls import path

from . import views


app_name = 'reviews_public'

urlpatterns = [
    path(
        'doctor/<uuid:doctor_id>/',
        views.DoctorReviewsView.as_view(),
        name='doctor-reviews',
    ),
    path(
        '',
        views.CreateAnonymousReviewView.as_view(),
        name='create-anonymous',
    ),
    path(
        'confirm/',
        views.ConfirmReviewView.as_view(),
        name='confirm',
    ),
]
