from django.http import JsonResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
import logging
import time

from .models import APIKey

logger = logging.getLogger(__name__)


class APIKeyMiddleware(MiddlewareMixin):
    """
    Middleware for API key authentication and validation.
    """
    
    # Endpoints that don't require API key authentication
    EXEMPT_PATHS = [
        '/admin/',
        '/api/v1/health/',
        '/api/v1/docs/',
    ]
    
    def process_request(self, request):
        """
        Process incoming request and validate API key if required.
        """
        # Skip API key validation for exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return None
        
        # Skip API key validation for non-API endpoints
        if not request.path.startswith('/api/'):
            return None
        
        # Get API key from header
        api_key_header = getattr(settings, 'API_KEY_HEADER', 'X-API-Key')
        api_key = request.META.get(f'HTTP_{api_key_header.upper().replace("-", "_")}')
        
        if not api_key:
            return self._error_response(
                'Missing API key. Please include your API key in the request header.',
                401,
                'missing_api_key'
            )
        
        # Validate API key
        is_valid, error_msg, api_key_obj = self._validate_api_key(api_key, request)
        
        if not is_valid:
            return self._error_response(error_msg, 403, 'invalid_api_key')
        
        # Attach API key object to request for use in views
        request.api_key = api_key_obj
        
        return None
    
    def _validate_api_key(self, api_key, request):
        """
        Validate the provided API key.
        
        Returns:
            tuple: (is_valid, error_message, api_key_object)
        """
        try:
            # Check cache first
            cache_key = f"api_key:{api_key}"
            cached_key = cache.get(cache_key)
            
            if cached_key:
                api_key_obj = cached_key
            else:
                try:
                    api_key_obj = APIKey.objects.get(key=api_key)
                    # Cache for 5 minutes
                    cache.set(cache_key, api_key_obj, 300)
                except APIKey.DoesNotExist:
                    return False, 'Invalid API key', None
            
            # Check if API key is valid
            if not api_key_obj.is_valid():
                return False, 'API key is inactive or expired', None
            
            # Check IP restrictions
            client_ip = self._get_client_ip(request)
            if not api_key_obj.is_ip_allowed(client_ip):
                return False, f'Access denied for IP address: {client_ip}', None
            
            # Check rate limits
            rate_limit_exceeded, limit_type = self._check_rate_limits(api_key_obj)
            if rate_limit_exceeded:
                return False, f'Rate limit exceeded: {limit_type}', None
            
            return True, None, api_key_obj
            
        except Exception as e:
            logger.error(f"Error validating API key: {str(e)}")
            return False, 'API key validation failed', None
    
    def _check_rate_limits(self, api_key_obj):
        """
        Check rate limits for the API key.
        
        Returns:
            tuple: (is_exceeded, limit_type)
        """
        try:
            current_time = int(time.time())
            
            # Check per-minute limit
            minute_key = f"rate_limit:minute:{api_key_obj.key}:{current_time // 60}"
            minute_count = cache.get(minute_key, 0)
            if minute_count >= api_key_obj.rate_limit_per_minute:
                return True, 'per-minute limit'
            
            # Check per-hour limit
            hour_key = f"rate_limit:hour:{api_key_obj.key}:{current_time // 3600}"
            hour_count = cache.get(hour_key, 0)
            if hour_count >= api_key_obj.rate_limit_per_hour:
                return True, 'per-hour limit'
            
            # Check per-day limit
            day_key = f"rate_limit:day:{api_key_obj.key}:{current_time // 86400}"
            day_count = cache.get(day_key, 0)
            if day_count >= api_key_obj.rate_limit_per_day:
                return True, 'per-day limit'
            
            # Increment counters
            cache.set(minute_key, minute_count + 1, 60)
            cache.set(hour_key, hour_count + 1, 3600)
            cache.set(day_key, day_count + 1, 86400)
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {str(e)}")
            return False, None
    
    def _get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _error_response(self, message, status_code, error_type):
        """Return a standardized error response."""
        return JsonResponse({
            'success': False,
            'data': None,
            'error': {
                'code': status_code,
                'message': message,
                'type': error_type
            },
            'timestamp': time.time()
        }, status=status_code)


class DevelopmentAPIKeyMiddleware(MiddlewareMixin):
    """
    Development middleware that bypasses API key authentication.
    """
    
    def process_request(self, request):
        if not getattr(settings, 'DEBUG', False):
            return None
        
        # mock API key object for development
        class MockAPIKey:
            def __init__(self):
                self.key = getattr(settings, 'DEFAULT_API_KEY', 'dev-key')
                self.name = 'Development Key'
                self.rate_limit_per_minute = 1000
                self.rate_limit_per_hour = 10000
                self.rate_limit_per_day = 100000
            
            def increment_usage(self):
                pass
        
        exempt_paths = ['/admin/', '/api/v1/health/', '/api/v1/docs/']
        if any(request.path.startswith(path) for path in exempt_paths):
            return None
        
        if not request.path.startswith('/api/'):
            return None
        
        # Attach mock API key to request
        request.api_key = MockAPIKey()
        
        return None
