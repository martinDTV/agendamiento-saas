"""URLs autenticadas de reviews. Las públicas viven en public_urls.py."""
from django.urls import path

from . import views


app_name = 'reviews'

urlpatterns = [
    path('', views.CreateReviewView.as_view(), name='create'),
]
