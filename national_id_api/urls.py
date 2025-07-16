from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from datetime import datetime

def api_root(request):
    """
    API root endpoint with basic information.
    """
    return JsonResponse({
        'success': True,
        'data': {
            'title': 'Egyptian National ID Validator API',
            'version': '1.0.0',
            'description': 'API for validating Egyptian National IDs and extracting relevant data',
            'endpoints': {
                'validate': '/api/v1/validate/',
                'bulk_validate': '/api/v1/validate/bulk/',
                'health': '/api/v1/health/',
                'documentation': '/api/v1/docs/',
            },
            'authentication': 'API Key required (X-API-Key header)',
            'rate_limits': 'Per API key - check documentation for details'
        },
        'error': None,
        'timestamp': datetime.now().isoformat()
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', cache_page(60 * 5)(api_root), name='api_root'),
    path('api/v1/', include('validator.urls')),
    path('', cache_page(60 * 15)(api_root), name='root'),
]
