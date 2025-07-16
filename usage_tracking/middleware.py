from django.utils.deprecation import MiddlewareMixin
import uuid
import json
import time
import logging

from .models import APICallLog

logger = logging.getLogger(__name__)


class UsageTrackingMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive API usage tracking and logging.
    """
    
    def process_request(self, request):
        """
        Initialize tracking for incoming request.
        """
        # Generate unique request ID
        request.tracking_id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # Store request details for logging
        request.tracking_data = {
            'request_id': request.tracking_id,
            'method': request.method,
            'path': request.path,
            'endpoint': self._get_endpoint_name(request.path),
            'query_params': dict(request.GET),
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        }
        
        # Capture request body for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if hasattr(request, 'body'):
                    # Store raw body but limit size for logging
                    body = request.body.decode('utf-8')
                    if len(body) > 10000:  # Limit to 10KB for logging
                        body = body[:10000] + '... [truncated]'
                    request.tracking_data['request_body'] = body
                    request.tracking_data['request_size_bytes'] = len(request.body)
            except Exception as e:
                logger.warning(f"Could not capture request body: {str(e)}")
        
        return None
    
    def process_response(self, request, response):
        """
        Log successful API calls.
        """
        # Skip tracking for non-API endpoints
        if not request.path.startswith('/api/'):
            return response
        
        try:
            self._log_api_call(request, response)
            self._update_api_key_usage(request, response)
        except Exception as e:
            logger.error(f"Error in usage tracking: {str(e)}")
        
        return response
    
    
    def _log_api_call(self, request, response):
        """
        Log the API call to the database.
        """
        if not hasattr(request, 'tracking_data'):
            return
        
        try:
            # Calculate response time
            response_time_ms = None
            if hasattr(request, 'start_time'):
                response_time_ms = (time.time() - request.start_time) * 1000
            
            # Get API key if available
            api_key = getattr(request, 'api_key', None)
            
            # Capture response details
            response_body = ''
            response_size_bytes = 0
            
            if hasattr(response, 'content'):
                response_size_bytes = len(response.content)
                # Only log response body for errors or if it's small
                if response.status_code >= 400 or response_size_bytes < 1000:
                    try:
                        response_body = response.content.decode('utf-8')
                    except:
                        response_body = '[Binary content]'
            
            # Extract validation results for National ID endpoints
            validation_successful = None
            national_id_count = 0
            cache_hit = False
            
            if response.status_code == 200 and hasattr(response, 'data'):
                try:
                    data = json.loads(response.content) if isinstance(response.content, bytes) else response.data
                    if isinstance(data, dict):
                        validation_successful = data.get('success', False)
                        cache_hit = data.get('cached', False)
                        
                        # Count national IDs processed
                        if 'data' in data and data['data']:
                            if 'results' in data['data']:  # Bulk validation
                                national_id_count = len(data['data']['results'])
                            elif 'national_id' in data['data']:  # Single validation
                                national_id_count = 1
                except:
                    pass
            
            # Create log entry
            if api_key and hasattr(api_key, 'id'):  # Only log for real API keys
                APICallLog.objects.create(
                    api_key=api_key,
                    request_id=request.tracking_data['request_id'],
                    endpoint=request.tracking_data['endpoint'],
                    method=request.tracking_data['method'],
                    path=request.tracking_data['path'],
                    query_params=json.dumps(request.tracking_data['query_params']),
                    ip_address=request.tracking_data['ip_address'],
                    user_agent=request.tracking_data['user_agent'],
                    referer=request.tracking_data['referer'],
                    request_body=request.tracking_data.get('request_body', ''),
                    request_size_bytes=request.tracking_data.get('request_size_bytes'),
                    status_code=response.status_code,
                    response_body=response_body,
                    response_size_bytes=response_size_bytes,
                    response_time_ms=response_time_ms,
                    validation_successful=validation_successful,
                    national_id_count=national_id_count,
                    cache_hit=cache_hit,
                )
            
        except Exception as e:
            logger.error(f"Error logging API call: {str(e)}")
    
    def _update_api_key_usage(self, request, response):
        """
        Update API key usage statistics.
        """
        api_key = getattr(request, 'api_key', None)
        if api_key and hasattr(api_key, 'increment_usage') and hasattr(api_key, 'id'):
            try:
                api_key.increment_usage()
            except Exception as e:
                logger.error(f"Error updating API key usage: {str(e)}")
    
    def _get_endpoint_name(self, path):
        """
        Extract endpoint name from path for better categorization.
        """
        # Normalize path for logging
        if path.startswith('/api/v1/'):
            endpoint = path.replace('/api/v1/', '')
            # Remove trailing slash
            endpoint = endpoint.rstrip('/')
            # Replace path parameters with placeholders
            if endpoint.startswith('validate/'):
                return 'validate'
            return endpoint
        return path
    
    def _get_client_ip(self, request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    