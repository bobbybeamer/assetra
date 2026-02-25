# Assetra Mobile Architecture (Native Android + iOS)

## Goals

- Offline-first scanning and asset updates
- Pluggable scan sources: camera, RFID SDK (`nur_sdk` style), external scanner
- Deferred sync with conflict handling
- Feature-flagged hardware capabilities per device profile

## Shared mobile architecture pattern

1. `ScanProvider` interface abstraction
   - `CameraScanProvider`
   - `RfidScanProvider` (SDK-backed)
   - `EnterpriseScannerProvider`
2. `LocalStore` for offline queue (Room on Android, Core Data/SQLite on iOS)
3. `SyncEngine` background worker
   - Push local events with `client_event_id`
   - Pull asset changes since `last_sync_at`
   - Resolve conflicts with `last-write-wins` + local conflict journal
4. `FeatureFlagService`
   - Pull server flags from `DeviceProfile` / `FeatureFlag`
   - Toggle SDK paths at runtime

## Device integration (scan providers)

Reference stubs for scan providers:
- Android: `mobile/android/scan/ScanProviders.kt`
- iOS: `mobile/ios/ScanProvider.swift`

Providers included:
- `CameraScanProvider`
- `RfidScanProvider`
- `EnterpriseScannerProvider`

## SDK client samples

Reference implementations for the sync client live in:
- Android: `mobile/android/AssetraApi.kt`
- iOS: `mobile/ios/AssetraAPI.swift`

Both clients:
- Call `POST /api/v1/sync/`
- Send `Authorization: Bearer <token>` and `X-Tenant-ID: <tenant_id>` headers
- Use `last_sync_at` and `scan_events` payload fields
- Retry once on `401` by refreshing the access token

Batch upload and de-duplication:
- Each scan event includes a `client_event_id` (UUID on device)
- The server deduplicates events by `client_event_id`
- Safe to retry the same batch if the network drops

Conflict acknowledgements:
- Send `conflict_acknowledgements` in the next sync after user resolution
- Each acknowledgement includes `conflict_id`, `resolution`, and `resolved_at`

Example payload:

```json
POST /api/v1/sync/
{
   "last_sync_at": "2026-02-25T18:45:00Z",
   "scan_events": [
      {
         "client_event_id": "3f0b8f7a-84e2-4f8e-9f3c-1dbe2e6d5a0d",
         "symbology": "qr",
         "raw_value": "QR-100",
         "source_type": "camera",
         "captured_at": "2026-02-25T18:44:58Z"
      },
      {
         "client_event_id": "a44b37f1-4930-4e4a-9e9e-2f9a8c10ad35",
         "symbology": "qr",
         "raw_value": "QR-101",
         "source_type": "camera",
         "captured_at": "2026-02-25T18:44:59Z"
      }
   ]
}
```

Authentication sample clients:
- Android: `mobile/android/AuthSample.kt`
- iOS: `mobile/ios/AuthSample.swift`

Both auth samples:
- Obtain JWT tokens via `POST /api/v1/auth/token/`
- Refresh tokens via `POST /api/v1/auth/token/refresh/`

Runnable sample modules (auth + capture + sync):
- Android: `mobile/android/SampleApp.kt`
- iOS: `mobile/ios/SampleApp.swift`

UI hook samples:
- Android Activity: `mobile/android/SampleActivity.kt`
- iOS SwiftUI view: `mobile/ios/SampleSyncView.swift`

Conflict resolution UI samples:
- Android Activity: `mobile/android/ConflictResolutionActivity.kt`
- iOS SwiftUI view: `mobile/ios/ConflictResolutionView.swift`

### How to run (Android)

Register the activity in your Android manifest:

```xml
<activity android:name="com.assetra.sample.SampleActivity" />
```

Launch it from an existing activity:

```kotlin
startActivity(Intent(this, SampleActivity::class.java))
```

### How to run (iOS)

Use the SwiftUI view as a root view:

```swift
@main
struct AssetraSampleApp: App {
   var body: some Scene {
      WindowGroup {
         SampleSyncView()
      }
   }
}
```

## End-to-end demo flow (Auth -> Capture -> Sync)

This flow shows how to wire the pieces together in a minimal app:

### Android (Kotlin)

```kotlin
val authClient = AuthClient(baseUrl = "https://api.assetra.example")
val tokenStore = InMemoryTokenStore()

val initial = authClient.login("user", "pass")
tokenStore.save(initial)

val tokenProvider = object : AccessTokenProvider {
   override fun accessToken(): String = tokenStore.load()?.access ?: ""

   override fun refreshAccessToken(): String {
      val current = tokenStore.load() ?: return ""
      val refreshed = authClient.refresh(current.refresh)
      tokenStore.save(refreshed)
      return refreshed.access
   }
}

val api = AssetraApi(
   baseUrl = "https://api.assetra.example",
   tenantId = "1",
   tokenProvider = tokenProvider,
)
val localStore = InMemoryLocalStore()
sampleCapture(localStore, rawValue = "QR-100")

val engine = OfflineSyncEngine(localStore, api)
engine.sync()
```

### iOS (Swift)

```swift
let authClient = AuthClient(baseURL: URL(string: "https://api.assetra.example")!)
let tokenStore = InMemoryTokenStore()

let initial = try await authClient.login(username: "user", password: "pass")
tokenStore.save(initial)

struct TokenProvider: AccessTokenProvider {
   let store: TokenStore
   let auth: AuthClient

   func accessToken() -> String {
      store.load()?.access ?? ""
   }

   func refreshAccessToken() async throws -> String {
      let current = store.load()
      let refreshed = try await auth.refresh(refreshToken: current?.refresh ?? "")
      store.save(refreshed)
      return refreshed.access
   }
}

let api = AssetraAPI(
   baseURL: URL(string: "https://api.assetra.example")!,
   tenantId: "1",
   tokenProvider: TokenProvider(store: tokenStore, auth: authClient)
)
let localStore = InMemoryLocalStore()
sampleCapture(localStore: localStore, rawValue: "QR-100")

let engine = OfflineSyncEngine(store: localStore, api: api)
try await engine.sync()
```

## Conflict resolution strategy

- Server is source of truth for final state
- Each update writes immutable history entry (`AssetStateHistory`)
- Clients keep pending operations with timestamps
- If server returns newer `updated_at`, client marks a conflict record and replays workflow steps if needed

## Security

- JWT access + refresh tokens
- Per-tenant header: `X-Tenant-ID`
- Device registration ties app installation to `DeviceProfile`
