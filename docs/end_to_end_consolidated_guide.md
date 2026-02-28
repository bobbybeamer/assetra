# Assetra End-to-End Consolidated Guide

## 1) What we have built

Assetra now runs as a multi-tenant operations platform with:

- Django + DRF backend API with JWT auth and tenant RBAC
- React web console for operations (assets + sync)
- Android and iOS mobile clients with offline sync patterns
- Role-aware UX for web users (read-only vs write-capable)

### Core architecture

- **Backend API**: [assetra_platform/urls.py](assetra_platform/urls.py), [assetra/views.py](assetra/views.py), [assetra/permissions.py](assetra/permissions.py)
- **RBAC model**: [assetra/models.py](assetra/models.py) (`TenantMembership.Role`)
- **Web app**: [web/src/App.tsx](web/src/App.tsx) and role-aware pages/components
- **Mobile sync clients**:
  - Android: [mobile/android/AssetraApi.kt](mobile/android/AssetraApi.kt)
  - iOS: [mobile/ios/AssetraAPI.swift](mobile/ios/AssetraAPI.swift)

### Key product capabilities delivered

1. **JWT + tenant-scoped auth flow** (web + mobile)
2. **Tenant RBAC enforcement** on backend (`admin`/`operator` write; `auditor`/`read_only` read)
3. **Role-aware web UX** (hides/disables create/edit/bulk/sync execution for read-only users)
4. **Assets workspace UX**:
   - search/filter/sort
   - pagination
   - inline edit
   - bulk status update
   - CSV export of current view
   - activity feed
5. **Sync workspace UX**:
   - run sync
   - summary metrics
   - optional raw payload view
6. **Operational reliability updates**:
   - CORS configured for local web dev + custom tenant header
   - stronger secret-key guidance and defaults

---

## 2) Current readiness status

### Backend

- Healthy in local sqlite mode
- `manage.py check` passes
- API smoke path verified (auth, assets, sync)

### Web

- Production build passes (`npm run build`)
- Role-aware UI is active using auth context endpoint

### Android

- Debug and release build/smoke flows completed in this environment
- Emulator launch and route checks were previously validated

### iOS

- Simulator release build/launch previously validated
- Full signed archive/device release is still dependent on Apple signing/team/profile setup

---

## 3) Important API and role endpoints

- `POST /api/v1/auth/token/`
- `POST /api/v1/auth/token/refresh/`
- `GET /api/v1/auth/context/` (new role context; returns `role` + `can_write`)
- `GET/POST /api/v1/assets/`
- `POST /api/v1/sync/`
- `GET /health/`

Role context implementation is in [assetra/views.py](assetra/views.py) and route in [assetra_platform/urls.py](assetra_platform/urls.py).

---

## 4) Local setup (backend + web)

## Prereqs

- Python 3.13+ with venv
- Node.js 20+
- npm

## Backend run (sqlite dev mode)

From repo root:

```bash
source .venv/bin/activate
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py migrate
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py runserver 127.0.0.1:8000
```

## Optional backend sanity check

```bash
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py check
```

## Seed role test users (idempotent)

```bash
DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py seed_role_users --tenant-id 1
```

Management command location: [assetra/management/commands/seed_role_users.py](assetra/management/commands/seed_role_users.py)

Seeded users:

- `std_readonly` / `StdUserPass123!`
- `std_operator` / `StdUserPass123!`

## Web app run

In another terminal:

```bash
cd web
npm install
npm run dev
```

Default URL: `http://127.0.0.1:5173`

Web app API client lives in [web/src/lib/api.ts](web/src/lib/api.ts).

---

## 5) How role-aware web behavior works

1. User signs in via JWT
2. Web app calls `GET /api/v1/auth/context/` with `Authorization` + `X-Tenant-ID`
3. Returned `can_write` drives UI gating:
   - **Write users** (`admin`, `operator`): see create/edit/bulk/sync-run actions
   - **Read-only users** (`auditor`, `read_only`): can view data but write controls are hidden/disabled

Relevant files:

- auth state: [web/src/hooks/useAuth.ts](web/src/hooks/useAuth.ts)
- app wiring: [web/src/App.tsx](web/src/App.tsx)
- assets gating: [web/src/pages/AssetsPage.tsx](web/src/pages/AssetsPage.tsx)
- sync gating: [web/src/pages/SyncPage.tsx](web/src/pages/SyncPage.tsx)

---

## 6) End-to-end web test script

## A. Admin/operator path

- Login with `smoke_admin` or `std_operator`
- Confirm role/access shown in header/cards
- Verify you can:
  - create asset
  - edit asset inline
  - run bulk status update
  - run sync

## B. Read-only path

- Login with `std_readonly`
- Confirm role/access indicates read-only
- Verify:
  - assets list/detail still visible
  - create/edit/bulk/sync-run controls are disabled/hidden
  - attempting write directly via API returns `403`

---

## 7) Android testing with backend (and web side-by-side)

Detailed mobile checklist reference: [docs/MOBILE_TESTING.md](docs/MOBILE_TESTING.md)

## Android app prerequisites

- Android Studio
- Emulator/device with camera support if testing camera provider

## Connectivity rules

- Android emulator to host backend: usually `http://10.0.2.2:8000`
- Physical Android device: `http://<your-computer-lan-ip>:8000`

## Android flow

1. Start backend (`127.0.0.1:8000`)
2. Run Android app from `mobile/android_app`
3. In app sync/auth fields use:
   - Base URL = emulator/device-reachable backend URL
   - Tenant ID = `1`
   - Username/password = test account
4. Execute:
   - sign in
   - camera/enterprise simulated scan (if applicable)
   - sync push/pull
5. In parallel, watch web UI (`/assets` and `/sync`) for reflected changes

Android sync client path: [mobile/android/AssetraApi.kt](mobile/android/AssetraApi.kt)

---

## 8) iOS testing with backend (and web side-by-side)

Detailed mobile checklist reference: [docs/MOBILE_TESTING.md](docs/MOBILE_TESTING.md)

## iOS app prerequisites

- Xcode 15+
- iOS simulator or physical device

## Connectivity rules

- iOS simulator can generally use `http://127.0.0.1:8000`
- Physical iOS device should use `http://<your-computer-lan-ip>:8000`

## iOS flow

1. Start backend (`127.0.0.1:8000`)
2. Open iOS app/project and run sample/production test target
3. Configure in app:
   - Base URL reachable from simulator/device
   - Tenant ID `1`
   - credentials (`smoke_admin`, `std_operator`, or `std_readonly`)
4. Execute:
   - sign in
   - scan simulation/camera as available
   - sync push/pull
5. Validate updates in web UI and backend responses

iOS sync client path: [mobile/ios/AssetraAPI.swift](mobile/ios/AssetraAPI.swift)

---

## 9) Full cross-platform E2E scenario (recommended)

1. Start backend
2. Start web app
3. Login web as admin/operator
4. Create an asset in web
5. Open Android app, login as same tenant user, run sync
6. Open iOS app, login, run sync
7. Back in web:
   - verify asset/sync payload changes
   - verify role behavior by re-login as `std_readonly`
8. Confirm read-only account cannot mutate data (UI + API)

This gives confidence that mobile + web all operate against the same backend/tenant model.

---

## 10) Troubleshooting

## CORS / browser fetch errors

- Confirm backend has `django-cors-headers` configured in [assetra_platform/settings.py](assetra_platform/settings.py)
- Ensure allowed origins include your web dev origin
- Ensure `X-Tenant-ID` is allowed in CORS headers

## Auth works but writes fail

- Check role via `GET /api/v1/auth/context/`
- `read_only` and `auditor` are expected to fail writes with `403`

## Mobile cannot reach backend

- Verify you are not using `127.0.0.1` from Android emulator (use `10.0.2.2`)
- For physical devices, use host LAN IP and same network
- Confirm firewall allows inbound on backend port

## iOS archive/release blocked

- Requires Apple team/profile setup
- Use existing recovery/checklist docs:
  - [docs/mobile_ios_step4_signing_recovery_checklist.md](docs/mobile_ios_step4_signing_recovery_checklist.md)
  - [mobile/ios_app/exportOptions.plist](mobile/ios_app/exportOptions.plist)

---

## 11) What “ready” means right now

For local/dev and internal QA, the stack is ready:

- backend + web + role RBAC + mobile sync flows are integrated
- role-aware web UX is implemented and validated
- Android path has been smoke-tested in this environment
- iOS simulator path has been validated

For full production release readiness, complete iOS signing/device release steps and any deployment hardening specific to your environment.
