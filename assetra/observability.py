"""Observability module: logging, metrics, health checks."""

import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime

from django.conf import settings
from django.db import connections
from prometheus_client import Counter, Histogram, Gauge


# ============================================================================
# STRUCTURED LOGGING
# ============================================================================

class JSONFormatter(logging.Formatter):
    """Structured JSON logging formatter."""

    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'tenant_id'):
            log_obj['tenant_id'] = record.tenant_id
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'duration_ms'):
            log_obj['duration_ms'] = record.duration_ms
        if hasattr(record, 'status_code'):
            log_obj['status_code'] = record.status_code
        
        return json.dumps(log_obj)


def configure_logging():
    """Configure structured logging for production."""
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(JSONFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [json_handler]
    
    # Suppress verbose third-party logs
    logging.getLogger('django.db.backends').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


# ============================================================================
# METRICS
# ============================================================================

# API metrics
api_requests_total = Counter(
    'assetra_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration_seconds = Histogram(
    'assetra_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Workflow metrics
workflow_executions_total = Counter(
    'assetra_workflow_executions_total',
    'Total workflow executions',
    ['workflow_name', 'status']
)

workflow_execution_duration_seconds = Histogram(
    'assetra_workflow_execution_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_name'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Webhook metrics
webhook_deliveries_total = Counter(
    'assetra_webhook_deliveries_total',
    'Total webhook deliveries',
    ['endpoint_id', 'status']
)

webhook_delivery_duration_seconds = Histogram(
    'assetra_webhook_delivery_duration_seconds',
    'Webhook delivery duration in seconds',
    ['endpoint_id'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

webhook_dead_letters_total = Counter(
    'assetra_webhook_dead_letters_total',
    'Total dead-lettered webhooks',
    ['endpoint_id']
)

# Task queue metrics
celery_tasks_total = Counter(
    'assetra_celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_pending_tasks = Gauge(
    'assetra_celery_pending_tasks',
    'Number of pending Celery tasks'
)

# Database metrics
db_connections_active = Gauge(
    'assetra_db_connections_active',
    'Active database connections'
)

db_query_duration_seconds = Histogram(
    'assetra_db_query_duration_seconds',
    'Database query duration in seconds',
    buckets=(0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0)
)


@contextmanager
def track_workflow_execution(workflow_name: str):
    """Context manager to track workflow execution metrics."""
    start_time = time.time()
    logger = logging.getLogger('assetra.workflow')
    
    try:
        yield
        duration = time.time() - start_time
        workflow_execution_duration_seconds.labels(workflow_name=workflow_name).observe(duration)
        workflow_executions_total.labels(workflow_name=workflow_name, status='success').inc()
        logger.info('Workflow executed', extra={
            'workflow_name': workflow_name,
            'duration_ms': int(duration * 1000),
            'status': 'success'
        })
    except Exception as exc:
        duration = time.time() - start_time
        workflow_executions_total.labels(workflow_name=workflow_name, status='error').inc()
        logger.error('Workflow failed', extra={
            'workflow_name': workflow_name,
            'duration_ms': int(duration * 1000),
            'status': 'error',
            'error': str(exc)
        })
        raise


@contextmanager
def track_webhook_delivery(endpoint_id: int, delivery_id: int = None):
    """Context manager to track webhook delivery metrics."""
    start_time = time.time()
    logger = logging.getLogger('assetra.webhook')
    
    try:
        yield
        duration = time.time() - start_time
        webhook_delivery_duration_seconds.labels(endpoint_id=str(endpoint_id)).observe(duration)
        webhook_deliveries_total.labels(endpoint_id=str(endpoint_id), status='success').inc()
        logger.info('Webhook delivered', extra={
            'endpoint_id': endpoint_id,
            'delivery_id': delivery_id,
            'duration_ms': int(duration * 1000),
            'status': 'success'
        })
    except Exception as exc:
        duration = time.time() - start_time
        webhook_deliveries_total.labels(endpoint_id=str(endpoint_id), status='error').inc()
        logger.error('Webhook delivery failed', extra={
            'endpoint_id': endpoint_id,
            'delivery_id': delivery_id,
            'duration_ms': int(duration * 1000),
            'status': 'error',
            'error': str(exc)
        })
        raise


# ============================================================================
# HEALTH CHECKS
# ============================================================================

def check_database() -> dict:
    """Check database connectivity and pool status."""
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT 1")
        return {
            'status': 'healthy',
            'component': 'database',
            'pool_size': getattr(connections['default'], 'pool_size', None),
        }
    except Exception as exc:
        return {
            'status': 'unhealthy',
            'component': 'database',
            'error': str(exc),
        }


def check_celery() -> dict:
    """Check Celery worker and broker connectivity."""
    try:
        from celery import current_app
        
        # Check broker connectivity
        broker_conn = current_app.connection()
        broker_conn.connect()
        broker_conn.close()
        
        # Check if workers are available
        from celery.app.utils import Settings
        worker_stats = current_app.control.inspect().stats()
        
        if not worker_stats:
            return {
                'status': 'degraded',
                'component': 'celery',
                'message': 'No workers available',
            }
        
        return {
            'status': 'healthy',
            'component': 'celery',
            'workers': len(worker_stats),
        }
    except Exception as exc:
        return {
            'status': 'unhealthy',
            'component': 'celery',
            'error': str(exc),
        }


def check_cache() -> dict:
    """Check cache (Redis) connectivity."""
    try:
        from django.core.cache import cache
        cache.set('_health_check', 'ok', 10)
        cache.get('_health_check')
        return {
            'status': 'healthy',
            'component': 'cache',
        }
    except Exception as exc:
        return {
            'status': 'unhealthy',
            'component': 'cache',
            'error': str(exc),
        }


def health_check_all() -> dict:
    """Comprehensive health check across all components."""
    checks = {}
    
    # Always check database
    checks['database'] = check_database()
    
    # Check Celery if not in eager mode
    if not settings.CELERY_TASK_ALWAYS_EAGER:
        checks['celery'] = check_celery()
    
    # Check cache if available
    try:
        checks['cache'] = check_cache()
    except ImportError:
        pass
    
    # Overall status
    overall = 'healthy'
    for check in checks.values():
        if check['status'] == 'unhealthy':
            overall = 'unhealthy'
            break
        elif check['status'] == 'degraded':
            overall = 'degraded'
    
    return {
        'status': overall,
        'timestamp': datetime.utcnow().isoformat(),
        'checks': checks,
    }
