from rest_framework.views import exception_handler
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Get the view and request for context
        view = context.get('view')
        request = context.get('request')
        
        # Log the error
        logger.error(
            f"API Error in {view.__class__.__name__}: {exc} "
            f"- Path: {request.path if request else 'N/A'} "
            f"- Method: {request.method if request else 'N/A'}"
        )
        
        # Create custom error response
        custom_response_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': get_error_message(exc, response),
                'type': exc.__class__.__name__,
            },
            'data': None,
            'timestamp': None  # Will be set by middleware
        }
        
        response.data = custom_response_data
    
    return response


def get_error_message(exc, response):
    """
    Extract appropriate error message from exception.
    """
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # Handle field-specific errors
            messages = []
            for field, errors in exc.detail.items():
                if isinstance(errors, list):
                    for error in errors:
                        messages.append(f"{field}: {error}")
                else:
                    messages.append(f"{field}: {errors}")
            return '; '.join(messages)
        elif isinstance(exc.detail, list):
            return '; '.join(str(error) for error in exc.detail)
        else:
            return str(exc.detail)
    
    return str(exc)


class ValidationError(Exception):
    """Custom validation error for National ID validation."""
    
    def __init__(self, message, code=None):
        self.message = message
        self.code = code or 'validation_error'
        super().__init__(self.message)


class RateLimitExceeded(Exception):
    """Custom exception for rate limit exceeded."""
    
    def __init__(self, message="Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)


class InvalidAPIKey(Exception):
    """Custom exception for invalid API key."""
    
    def __init__(self, message="Invalid or missing API key"):
        self.message = message
        super().__init__(self.message)
