# Operations & Monitoring Guide

This guide explains how to run and monitor Assetra in production with the
Prometheus + Grafana + Alertmanager stack.

## Stack Overview

The production stack includes:
- Assetra web service (Django + Gunicorn)
- Celery worker + beat
- PostgreSQL
- Redis
- Prometheus (metrics scraping)
- Grafana (dashboards)
- Alertmanager (alert routing)

## Environment Variables

Set these in `.env` or your secret manager:

- `SENTRY_DSN`: Sentry project DSN (optional)
- `SENTRY_TRACES_SAMPLE_RATE`: 0.0 - 1.0 sampling rate (default 0.1)
- `ENVIRONMENT`: `development`, `staging`, `production`
- `GRAFANA_PASSWORD`: default admin password

## Start the Production Stack

```bash
cp .env.example .env
# Edit .env for DB credentials, Sentry DSN, Grafana password

docker compose -f docker-compose.prod.yml up --build
```

## Local (No Docker) Verification

You can validate health and metrics locally without Docker by running the Django
dev server with SQLite and eager Celery tasks:

```bash
source .venv/bin/activate
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py migrate
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py runserver 127.0.0.1:8000
```

Then verify endpoints:

```bash
curl -s http://127.0.0.1:8000/health/ | python3 -m json.tool
curl -s http://127.0.0.1:8000/alive/
curl -s http://127.0.0.1:8000/metrics/ | head -30
```

## Health & Metrics

- Health check: `GET /health/`
- Liveness probe: `GET /alive/`
- Metrics: `GET /metrics/`

Validate with:

```bash
curl -s http://localhost:8000/health/ | python3 -m json.tool
curl -s http://localhost:8000/alive/
curl -s http://localhost:8000/metrics/ | head -30
```

## Prometheus

Prometheus UI: http://localhost:9090

Key queries:

```promql
sum(rate(assetra_api_requests_total[1m]))
histogram_quantile(0.95, sum(rate(assetra_api_request_duration_seconds_bucket[5m])) by (le))
rate(assetra_webhook_dead_letters_total[5m])
```

## Grafana

Grafana UI: http://localhost:3000

Login:
- user: `admin`
- password: value of `GRAFANA_PASSWORD` (default `admin`)

Dashboard: **Assetra Observability**

## Alertmanager

Alertmanager UI: http://localhost:9093

Configure integrations in [monitoring/alertmanager.yml](../monitoring/alertmanager.yml)

## Common Issues

**No metrics appear in Grafana**
- Verify Prometheus is scraping `/metrics/`
- Ensure `web:8000` is accessible from Prometheus container

**Health check returns 503**
- Check database connectivity and Redis
- Verify Celery workers are running

**Sentry not receiving events**
- Confirm `SENTRY_DSN` is set
- Check outbound network access
