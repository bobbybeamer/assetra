"""Request tracking middleware for observability."""

import logging
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

from assetra.observability import api_requests_total, api_request_duration_seconds


class RequestTrackingMiddleware(MiddlewareMixin):
    """Track API requests with metrics and structured logging."""
    
    def process_request(self, request):
        """Start request tracking."""
        request.request_id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # Extract tenant_id from header
        request.tenant_id = request.META.get('HTTP_X_TENANT_ID')
        
        # Extract user_id if authenticated
        request.user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None
        
        logger = logging.getLogger('assetra.api')
        logger.info(
            f'{request.method} {request.path_info}',
            extra={
                'request_id': request.request_id,
                'tenant_id': request.tenant_id,
                'user_id': request.user_id,
            }
        )
    
    def process_response(self, request, response):
        """Record API metrics and response logging."""
        if not hasattr(request, 'start_time'):
            return response
        
        duration = time.time() - request.start_time
        
        # Extract endpoint (path without query string)
        endpoint = request.path_info.replace('/api/v1', '')
        
        # Record metrics
        api_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        api_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        # Log response
        logger = logging.getLogger('assetra.api')
        level = 'WARNING' if response.status_code >= 400 else 'INFO'
        logger_method = getattr(logger, level.lower())
        
        logger_method(
            f'{request.method} {request.path_info} -> {response.status_code}',
            extra={
                'request_id': getattr(request, 'request_id', None),
                'tenant_id': getattr(request, 'tenant_id', None),
                'user_id': getattr(request, 'user_id', None),
                'status_code': response.status_code,
                'duration_ms': int(duration * 1000),
            }
        )
        
        return response
