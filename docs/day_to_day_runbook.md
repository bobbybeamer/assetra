# Assetra Day-to-Day Runbook (5–10 Minutes)

This is the fast operational checklist for local dev + QA.

For full architecture and deep testing details, use [docs/end_to_end_consolidated_guide.md](docs/end_to_end_consolidated_guide.md).

## 1) Start backend (Terminal A)

From repo root:

```bash
source .venv/bin/activate
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py migrate
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py runserver 127.0.0.1:8000
```

Quick health check:

```bash
curl -s http://127.0.0.1:8000/health/
```

## 2) Seed role users once (or anytime, idempotent)

```bash
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py seed_role_users --tenant-id 1
```

Seeded test users:

- `smoke_admin` / `SmokePass123!` (admin)
- `std_operator` / `StdUserPass123!` (write user)
- `std_readonly` / `StdUserPass123!` (read-only user)

## 3) Start web app (Terminal B)

```bash
cd web
npm install
npm run dev
```

Open: `http://127.0.0.1:5173`

## 4) Web quick verification

## A. Operator/Admin test

Login as `smoke_admin` or `std_operator`:

- verify role/access shows write
- create an asset
- edit an asset inline
- run bulk update
- run sync

## B. Read-only test

Login as `std_readonly`:

- verify role/access shows read-only
- verify create/edit/bulk/sync-run controls are hidden or disabled
- verify you can still view assets/sync status

## 5) Android quick test

## Backend URL to use from Android

- Emulator: `http://10.0.2.2:8000`
- Physical device: `http://<your-lan-ip>:8000`

## Steps

- launch Android app
- configure:
  - Base URL = emulator/device reachable backend URL
  - Tenant ID = `1`
  - user = `smoke_admin` or `std_operator`
- sign in
- run scan simulation/camera flow
- run sync
- confirm web UI reflects updates

## 6) iOS quick test

## Backend URL to use from iOS

- Simulator: usually `http://127.0.0.1:8000`
- Physical device: `http://<your-lan-ip>:8000`

## Steps

- launch iOS app in Xcode
- configure:
  - Base URL reachable by simulator/device
  - Tenant ID = `1`
  - user = `smoke_admin` or `std_operator`
- sign in
- run scan simulation/camera flow
- run sync
- confirm web UI reflects updates

## 7) API role sanity check (optional)

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"std_readonly","password":"StdUserPass123!"}' \
  | python -c 'import sys,json; print(json.load(sys.stdin)["access"])')

curl -s http://127.0.0.1:8000/api/v1/auth/context/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Tenant-ID: 1'
```

Expected: `"role":"read_only"` and `"can_write":false`.

## 8) Done / shutdown

- stop web dev server
- stop Django server

## Troubleshooting (fast)

- Web login/fetch fails:
  - ensure backend is running on `127.0.0.1:8000`
  - ensure web is on `127.0.0.1:5173`
- Mobile cannot reach backend:
  - Android emulator must use `10.0.2.2`
  - physical devices must use LAN IP
- Write actions blocked unexpectedly:
  - call `/api/v1/auth/context/` and confirm role/can_write
