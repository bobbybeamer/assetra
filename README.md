# Assetra

Assetra is a multi-tenant barcode, asset tracking, and asset management platform scaffolded with Django + DRF.

## Architecture

- Backend: Django + Django REST Framework
- Auth: JWT (`simplejwt`)
- DB: PostgreSQL by default, optional MySQL/MariaDB via `DB_ENGINE`
- Async jobs: Celery
- Multi-tenant + RBAC: header-based tenant context (`X-Tenant-ID`) and membership roles (`admin`, `operator`, `auditor`, `read_only`)
- Mobile: native Android/iOS with offline-first sync flow (see docs)

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Docker Compose (production-style local stack)

```bash
cp .env.example .env
docker compose up --build
```

Services:

- `web` (Django + Gunicorn): http://localhost:8000
- `db` (PostgreSQL)
- `redis`
- `worker` (Celery worker)
- `beat` (Celery beat scheduler)

## Local Dev (No Docker)

Docker is optional for local development. You can run the app with SQLite and eager Celery tasks:

```bash
source .venv/bin/activate
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py migrate
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py runserver 127.0.0.1:8000
```

## API endpoints (examples)

- `POST /api/v1/auth/token/` - obtain JWT
- `POST /api/v1/auth/token/refresh/` - refresh JWT
- `GET/POST /api/v1/assets/`
- `GET/POST /api/v1/scan-events/`
- `GET/POST /api/v1/inventory-sessions/`
- `GET/POST /api/v1/workflow-definitions/`
- `POST /api/v1/workflow-definitions/{id}/execute/` - manual workflow execution/debug run
- `GET /api/v1/workflow-runs/` and `GET /api/v1/workflow-runs/{id}/` - run history and details
- `GET/POST /api/v1/form-definitions/`
- `GET/POST /api/v1/barcode-batches/`
- `GET/POST /api/v1/webhooks/`
- `POST /api/v1/sync/` - offline push/pull sync endpoint
- `POST /api/v1/barcodes/validate/` - validation + decode service
- `GET /api/v1/lookups/assets/?barcode=...` - live lookup URL
- `GET /api/v1/live-data/` - stream-friendly polling endpoint
- `POST /api/v1/webhooks/inbound/` - inbound webhook receiver

## OpenAPI

- Raw schema: `GET /api/schema/`
- Swagger UI: `GET /api/docs/swagger/`
- ReDoc: `GET /api/docs/redoc/`

Export schema file:

```bash
python manage.py spectacular --file schema.yaml
```

## CI/CD

- CI workflow: `.github/workflows/ci.yml`
	- Runs checks, migrations, tests, and schema generation on push/PR.
- Release workflow: `.github/workflows/release.yml`
	- Triggers on tags like `v1.0.0` or manual dispatch.
	- Builds and pushes Docker image to `ghcr.io/<owner>/assetra`.
	- Attaches versioned OpenAPI schema to the GitHub Release.

Tag release example:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Smoke Testing

Reusable script:

```bash
source .venv/bin/activate
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py runserver 127.0.0.1:8000
```

In another terminal:

```bash
source .venv/bin/activate
python scripts/smoke_test.py --base-url http://127.0.0.1:8000 --username smoke_admin --password 'SmokePass123!' --tenant-id 1
```

The script validates: auth → asset create → scan create → sync → webhook create → inbound webhook → barcode validation → lookup.

## Postman Collection

- Collection file: `postman/Assetra.postman_collection.json`
- Import it in Postman and run in order from `01` to `08`.
- Collection variables included: `baseUrl`, `username`, `password`, `tenantId`.
- Runtime variables automatically set by tests: `accessToken`, `assetId`, `barcodeValue`, `webhookEndpointId`.

## Stage 2: Productization (Workflow Validation, Webhook Reliability, RBAC Hardening)

### Workflow Validation & Dry-Run

Workflow definitions are validated on create/update for:
- Valid `trigger_type` (e.g., `on_scan`, `on_status_change`, `manual`)
- Valid entry conditions with proper field/operator/value combinations
- Step actions from the supported whitelist: `create_asset`, `update_asset_status`, `dispatch_webhook`, `create_audit_log`

**Workflow schema validation error example:**

```json
POST /api/v1/workflow-definitions/
{
	"name": "Invalid Workflow",
	"trigger_type": "invalid_trigger",
	"entry_conditions": [],
	"steps": []
}

// Response 400: {"trigger_type": ["Invalid trigger type. Supported: on_scan, on_status_change, manual"]}
```

**Dry-run mode** (preview without mutations):

```bash
POST /api/v1/workflow-definitions/123/execute/
{
	"asset_id": 100,
	"dry_run": true
}

// Response 200:
{
	"dry_run": true,
	"preview": {
		"matched_entry_conditions": [
			{
				"field": "asset_state",
				"operator": "equals",
				"value": "in_transit",
				"matched": true
			}
		],
		"simulated_steps": [
			{
				"action": "update_asset_status",
				"status": "in_warehouse",
				"success": true,
				"note": "Would update asset status"
			}
		],
		"message": "Dry-run successful. No database changes made."
	}
}
```

- `dry_run: true` simulates all steps and returns preview metadata
- **No database mutations**, no `WorkflowRun` record created
- Useful for testing workflows before deploying to production

### Webhook Reliability & Signing

**Outbound webhook signing:**

All outbound webhooks include a signed delivery with `X-Assetra-Signature` header (HMAC-SHA256):

```
X-Assetra-Signature: sha256=abc123def456...
X-Assetra-Timestamp: 1677000000

payload: {"event": "asset.created", "asset_id": 100, ...}
```

**Verify signature on receiving end:**

```python
import hmac
import hashlib

WEBHOOK_SECRET = "your-webhook-secret"

def verify_signature(request):
    signature_header = request.headers.get("X-Assetra-Signature")
    timestamp_header = request.headers.get("X-Assetra-Timestamp")
    body = request.get_data()
    
    # Reconstruct signed message
    signed_message = f"{timestamp_header}.{body.decode()}"
    
    # Compute HMAC-SHA256
    expected_sig = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        signed_message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(signature_header, expected_sig)
```

**Delivery reliability:**

- Field tracking: `attempt_count`, `next_attempt_at`, `last_error`, `dead_lettered_at`
- Status progression:
  - **2xx response** → `success` (delivery accepted)
  - **Transient error** (network timeout, 5xx) → `pending` + exponential backoff retry
  - **Max attempts exceeded** (5 by default) → `dead_letter` + alert for manual review
- Retry backoff: `min(base * 2^(attempts-1), 3600)` seconds (base=5s, max=1h)

**Check dead-lettered webhooks:**

```bash
GET /api/v1/webhooks/?status=dead_letter
```

### RBAC & Tenant Isolation

**Role matrix:**

| Role | Assets | Workflows | Webhooks | Write Access |
|------|--------|-----------|----------|--------------|
| `admin` | Full CRUD | Full CRUD | Full CRUD | ✅ Yes |
| `operator` | Full CRUD | Execute/view | Create/view | ✅ Yes |
| `auditor` | View only | View only | View only | ❌ No |
| `read_only` | View only | View only | View only | ❌ No |

**Tenant isolation:**

- All resources scoped to tenant via `tenant_id` field
- Multi-tenant context passed via `X-Tenant-ID` header
- Permission enforcement at two levels:
  - **Collection level** (`has_permission`): Validates user is tenant member with appropriate role
  - **Object level** (`has_object_permission`): Enforces object's `tenant_id` matches request context
- Cross-tenant access returns `403 Forbidden` (access denied)
- Foreign key validation: Assets, scan events, workflows must reference resources from the same tenant

**Example: Cross-tenant isolation test**

```bash
# User A requests asset owned by Tenant B with Tenant B credentials
GET /api/v1/assets/999/
Headers:
  Authorization: Bearer {user_a_token}
  X-Tenant-ID: {tenant_b_id}

// Response 403 Forbidden
{
	"detail": "You do not have permission to perform this action."
}
```

**Tenant-safe foreign key validation:**

Creating a scan event references an asset:

```json
POST /api/v1/scan-events/
{
	"asset": 100,  // Must belong to same tenant
	"symbology": "qr",
	"raw_value": "QR-100"
}

// If asset belongs to different tenant:
// Response 400: {"asset": ["Asset not found."]}
```

## Production Hardening (Observability & Monitoring)

### Structured Logging

All application logs are structured as JSON for easy parsing and aggregation:

```bash
GET /api/v1/assets/
# Log output (JSON):
# {"timestamp": "2026-02-25T17:57:38.800000", "level": "INFO", "logger": "assetra.api", 
#  "message": "GET /api/v1/assets/", "request_id": "abc-123", "tenant_id": "1", 
#  "user_id": 1, "status_code": 200, "duration_ms": 45}
```

**Log levels:**
- `INFO` - API requests, workflow executions, webhook deliveries
- `WARNING` - Non-2xx responses, transient errors, degraded service
- `ERROR` - Unhandled exceptions, failed operations

### Health Checks

**Full health check (all components):**

```bash
GET /health/

# Response 200 (healthy):
{
  "status": "healthy",
  "timestamp": "2026-02-25T17:57:44.619001",
  "checks": {
    "database": {
      "status": "healthy",
      "component": "database",
      "pool_size": 10
    },
    "cache": {
      "status": "healthy",
      "component": "cache"
    },
    "celery": {
      "status": "healthy",
      "component": "celery",
      "workers": 2
    }
  }
}

# Response 503 (unhealthy):
{
  "status": "unhealthy",
  "checks": {
    "database": {
      "status": "unhealthy",
      "error": "Connection refused"
    }
  }
}
```

**Liveness probe (for Kubernetes):**

```bash
GET /alive/

# Always returns 200 if process is alive
{ "status": "alive" }
```

### Prometheus Metrics

**Metrics endpoint:**

```bash
GET /metrics/
```

Exposed metrics:
- `assetra_api_requests_total{method, endpoint, status_code}` - API request count
- `assetra_api_request_duration_seconds{method, endpoint}` - Request latency (histogram)
- `assetra_workflow_executions_total{workflow_name, status}` - Workflow execution count
- `assetra_workflow_execution_duration_seconds{workflow_name}` - Workflow latency
- `assetra_webhook_deliveries_total{endpoint_id, status}` - Webhook delivery count
- `assetra_webhook_delivery_duration_seconds{endpoint_id}` - Delivery latency
- `assetra_webhook_dead_letters_total{endpoint_id}` - Dead-lettered webhook count
- `assetra_celery_pending_tasks` - Pending Celery task count
- `assetra_db_connections_active` - Active database connections
- `assetra_db_query_duration_seconds` - Database query latency

**Scrape configuration (Prometheus):**

```yaml
scrape_configs:
  - job_name: 'assetra'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/'
```

### Error Tracking with Sentry

Configure Sentry for exception tracking and alerting:

```bash
export SENTRY_DSN="https://examplePublicKey@o0.ingest.sentry.io/0"
export SENTRY_TRACES_SAMPLE_RATE="0.1"
export ENVIRONMENT="production"
```

All unhandled exceptions are automatically captured with:
- Full stack traces
- Request context (headers, user, tenant)
- Breadcrumbs (recent API calls, database queries)
- Release version for regression detection

### Monitoring Production Deployments

**Docker Compose with observability:**

```bash
# Stack includes: web, db, redis, worker, beat, prometheus, grafana
docker compose -f docker-compose.prod.yml up

# Access dashboards:
Open http://localhost:3000 (Grafana)
```

**Docker health checks:**

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 40s
```

**Kubernetes probes:**

```yaml
livenessProbe:
  httpGet:
    path: /alive/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Design highlights

- Immutable audit records via `AssetStateHistory` with checksum
- Offline event ingestion with `ScanEvent.client_event_id`
- Conflict strategy: last-write-wins with full history preservation
- Workflow engine primitives (`NoCodeFormDefinition`, `WorkflowDefinition`, `WorkflowRun`)
- Barcode template and batch generation (`BarcodeTemplate`, `BarcodeBatch`, `BarcodeLabel`)
- Integration primitives (`IntegrationConnector`, `WebhookEndpoint`, `WebhookDelivery`)
- Hardware abstraction support (`DeviceProfile.sdk_features` and `FeatureFlag`)

## Mobile architecture docs

- [Android/iOS architecture and sync notes](docs/mobile_architecture.md)
- [Android sample offline sync](mobile/android/OfflineSyncSample.kt)
- [iOS sample offline sync](mobile/ios/OfflineSyncSample.swift)
