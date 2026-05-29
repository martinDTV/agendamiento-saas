"""URLs públicas de la app places."""
from django.urls import path

from .views import BranchLocationView, PostalCodeLookupView


app_name = 'places'

urlpatterns = [
    path(
        'postal-code/<str:cp>/',
        PostalCodeLookupView.as_view(),
        name='postal-code-lookup',
    ),
    path(
        'branch/<uuid:branch_id>/location/',
        BranchLocationView.as_view(),
        name='branch-location',
    ),
]
