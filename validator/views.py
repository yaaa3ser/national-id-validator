from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db import connection
from django_ratelimit.decorators import ratelimit
from datetime import datetime
import time
import logging

from .egyptian_id_validator import EgyptianNationalIDValidator
from .serializers import NationalIDValidationSerializer

logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    
    def dispatch(self, request, *args, **kwargs):
        """Add request start time for performance monitoring."""
        request.start_time = time.time()
        return super().dispatch(request, *args, **kwargs)
    
    def finalize_response(self, request, response, *args, **kwargs):
        """Add processing time and timestamp to response."""
        response = super().finalize_response(request, response, *args, **kwargs)
        
        # Add timestamp and processing time to response
        if hasattr(request, 'start_time'):
            processing_time = (time.time() - request.start_time) * 1000
            
            if hasattr(response, 'data') and isinstance(response.data, dict):
                response.data['timestamp'] = datetime.now().isoformat()
                response.data['processing_time_ms'] = round(processing_time, 2)
        
        return response


@method_decorator(ratelimit(key='ip', rate='100/m', method='POST'), name='post')
class NationalIDValidationView(BaseAPIView):
    """
    API endpoint for validating Egyptian National IDs and extracting data.
    
    POST /api/v1/validate/
    
    Request Body:
    {
        "national_id": "29001011234567",
        "include_details": true
    }
    
    Response:
    {
        "success": true,
        "data": {
            "national_id": "29001011234567",
            "is_valid": true,
            "birth_date": "1990-01-01",
            "age": 34,
            "gender": "Male",
            "governorate": "Cairo",
            "governorate_code": "01",
            "century": "20th",
            "sequence_number": "1234",
            "validation_details": {
                "format_valid": true,
                "date_valid": true,
                "governorate_valid": true
            }
        },
        "error": null,
        "timestamp": "2025-07-16T10:30:00Z",
        "processing_time_ms": 5.23
    }
    """
    
    def post(self, request):
        """
        Validate Egyptian National ID and extract data.
        """
        try:
            # Validate input data
            serializer = NationalIDValidationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'data': None,
                    'error': {
                        'code': 400,
                        'message': 'Invalid input data',
                        'type': 'ValidationError',
                        'field_errors': serializer.errors
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            national_id = validated_data['national_id']
            include_details = validated_data.get('include_details', True)
            
            # Check cache first
            cache_key = f"national_id_validation:{national_id}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Returning cached result for national ID: {national_id[:4]}****{national_id[-2:]}")
                return Response({
                    'success': True,
                    'data': cached_result,
                    'error': None,
                    'cached': True
                })
            
            # Validate national ID
            validator = EgyptianNationalIDValidator()
            is_valid, extracted_data = validator.validate(national_id)
            
            if is_valid:
                # Filter response data based on include_details
                if not include_details:
                    extracted_data = {
                        'national_id': extracted_data['national_id'],
                        'is_valid': extracted_data['is_valid'],
                        'birth_date': extracted_data['birth_date'],
                        'age': extracted_data['age'],
                        'gender': extracted_data['gender']
                    }
                
                # Cache the result for 1 hour
                cache.set(cache_key, extracted_data, 3600)
                
                return Response({
                    'success': True,
                    'data': extracted_data,
                    'error': None
                })
            else:
                return Response({
                    'success': False,
                    'data': None,
                    'error': {
                        'code': 422,
                        'message': extracted_data.get('error', 'Validation failed'),
                        'type': 'ValidationError'
                    }
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        except Exception as e:
            logger.error(f"Unexpected error in validation: {str(e)}")
            return Response({
                'success': False,
                'data': None,
                'error': {
                    'code': 500,
                    'message': 'Internal server error',
                    'type': 'InternalServerError'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(ratelimit(key='ip', rate='50/m', method='POST'), name='post')
class BulkValidationView(BaseAPIView):
    """
    API endpoint for bulk validation of multiple National IDs.
    
    POST /api/v1/validate/bulk/
    
    Request Body:
    {
        "national_ids": ["29001011234567", "30012251234568"],
        "include_details": false
    }
    """
    
    def post(self, request):
        """
        Validate multiple Egyptian National IDs in bulk.
        """
        try:
            national_ids = request.data.get('national_ids', [])
            include_details = request.data.get('include_details', False)
            
            if not isinstance(national_ids, list):
                return Response({
                    'success': False,
                    'data': None,
                    'error': {
                        'code': 400,
                        'message': 'national_ids must be a list',
                        'type': 'ValidationError'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if len(national_ids) > 100:  # Limit bulk operations
                return Response({
                    'success': False,
                    'data': None,
                    'error': {
                        'code': 400,
                        'message': 'Maximum 100 national IDs allowed per request',
                        'type': 'ValidationError'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validator = EgyptianNationalIDValidator()
            results = []
            
            for national_id in national_ids:
                try:
                    # Basic input validation
                    serializer = NationalIDValidationSerializer(data={'national_id': national_id})
                    if not serializer.is_valid():
                        results.append({
                            'national_id': str(national_id),
                            'is_valid': False,
                            'error': 'Invalid format'
                        })
                        continue
                    
                    cleaned_id = serializer.validated_data['national_id']
                    is_valid, extracted_data = validator.validate(cleaned_id)
                    
                    if is_valid:
                        result = {
                            'national_id': extracted_data['national_id'],
                            'is_valid': True,
                            'birth_date': extracted_data['birth_date'],
                            'age': extracted_data['age'],
                            'gender': extracted_data['gender']
                        }
                        
                        if include_details:
                            result.update({
                                'governorate': extracted_data['governorate'],
                                'governorate_code': extracted_data['governorate_code'],
                                'century': extracted_data['century'],
                                'validation_details': extracted_data['validation_details']
                            })
                        
                        results.append(result)
                    else:
                        results.append({
                            'national_id': cleaned_id,
                            'is_valid': False,
                            'error': extracted_data.get('error', 'Validation failed')
                        })
                
                except Exception as e:
                    results.append({
                        'national_id': str(national_id),
                        'is_valid': False,
                        'error': f'Processing error: {str(e)}'
                    })
            
            return Response({
                'success': True,
                'data': {
                    'total_processed': len(results),
                    'results': results
                },
                'error': None
            })
        
        except Exception as e:
            logger.error(f"Unexpected error in bulk validation: {str(e)}")
            return Response({
                'success': False,
                'data': None,
                'error': {
                    'code': 500,
                    'message': 'Internal server error',
                    'type': 'InternalServerError'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(cache_page(60 * 5), name='get')  # Cache for 5 minutes
class HealthCheckView(BaseAPIView):
    """
    Health check endpoint for monitoring service status.
    
    GET /api/v1/health/
    """
    
    def get(self, request):
        """
        Check the health status of the service and its dependencies.
        """
        try:
            health_status = {
                'status': 'healthy',
                'version': '1.0.0',
                'database': 'unknown',
                'cache': 'unknown'
            }
            
            # Check database connection
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                health_status['database'] = 'healthy'
            except Exception as e:
                health_status['database'] = f'error: {str(e)}'
                health_status['status'] = 'degraded'
            
            # Check cache connection
            try:
                cache.set('health_check', 'test', 10)
                cache.get('health_check')
                health_status['cache'] = 'healthy'
            except Exception as e:
                health_status['cache'] = f'error: {str(e)}'
                health_status['status'] = 'degraded'
            
            return Response({
                'success': True,
                'data': health_status,
                'error': None
            })
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return Response({
                'success': False,
                'data': None,
                'error': {
                    'code': 500,
                    'message': 'Health check failed',
                    'type': 'InternalServerError'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def api_documentation(request):
    """
    API documentation endpoint.
    
    GET /api/v1/docs/
    """
    documentation = {
        'title': 'Egyptian National ID Validator API',
        'version': '1.0.0',
        'description': 'Professional API for validating Egyptian National IDs and extracting relevant data',
        'endpoints': {
            'POST /api/v1/validate/': {
                'description': 'Validate a single Egyptian National ID',
                'parameters': {
                    'national_id': 'string (required) - 14-digit Egyptian National ID',
                    'include_details': 'boolean (optional, default: true) - Include detailed validation info'
                },
                'rate_limit': '100 requests per minute per IP'
            },
            'POST /api/v1/validate/bulk/': {
                'description': 'Validate multiple Egyptian National IDs in bulk',
                'parameters': {
                    'national_ids': 'array of strings (required) - Up to 100 National IDs',
                    'include_details': 'boolean (optional, default: false) - Include detailed validation info'
                },
                'rate_limit': '50 requests per minute per IP'
            },
            'GET /api/v1/health/': {
                'description': 'Check service health status',
                'parameters': None,
                'rate_limit': 'No limit'
            }
        },
        'authentication': {
            'type': 'API Key',
            'header': 'X-API-Key',
            'description': 'Include your API key in the X-API-Key header'
        },
        'response_format': {
            'success': 'boolean - Indicates if the request was successful',
            'data': 'object - Response data (null on error)',
            'error': 'object - Error details (null on success)',
            'timestamp': 'string - ISO 8601 timestamp',
            'processing_time_ms': 'number - Request processing time in milliseconds'
        }
    }
    
    return Response({
        'success': True,
        'data': documentation,
        'error': None
    })
