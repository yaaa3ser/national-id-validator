"""
URL configuration for the validator app.
"""

from django.urls import path
from .views import (
    NationalIDValidationView,
    BulkValidationView,
    HealthCheckView,
    api_documentation
)

app_name = 'validator'

urlpatterns = [
    path('validate/', NationalIDValidationView.as_view(), name='validate'),
    path('validate/bulk/', BulkValidationView.as_view(), name='bulk_validate'),
    path('health/', HealthCheckView.as_view(), name='health'),
    path('docs/', api_documentation, name='documentation'),
]
