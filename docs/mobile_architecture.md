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

### Multi-SDK strategy (per platform)

Both Android and iOS scan providers support multiple SDK backends behind the same `ScanProvider` API.

- Register backends in order of preference (for example: hardware OEM SDK first, camera SDK second).
- At runtime, provider selects the first backend reporting availability.
- If primary hardware is unavailable on a device, provider falls back to the next backend automatically.
- This allows one app build to support mixed hardware fleets without changing sync contracts.

#### Android concrete adapters in this repo

`mobile/android/scan/ScanProviders.kt` now includes:

- `MlKitCameraBackend` (camera barcode path)
- `DataWedgeEnterpriseBackend` (enterprise scanner intent payload path)
- `parseDataWedgePayload(...)` helper for DataWedge payload keys

`mobile/android/scan/CameraXBarcodeSession.kt` provides a concrete CameraX + ML Kit session scaffold (`CameraXBarcodeSession`) with:
- camera permission request
- preview binding via `PreviewView`
- barcode analyzer callback wiring

Wiring pattern:

1. Build a `CameraScanSession` that wraps your ML Kit camera pipeline.
2. Build a `DataWedgeSession` that wraps your broadcast receiver registration.
3. Inject them into providers as preferred backends (hardware first, fallback second).

Example:

```kotlin
val dataWedgeSession = DataWedgeBroadcastSession(context = this)

val cameraProvider = CameraScanProvider(
   backends = listOf(
      MlKitCameraBackend(
         session = LambdaCameraSession(
            onStart = { onDecoded -> startMlKitPipeline(onDecoded) },
            onStop = { stopMlKitPipeline() }
         )
      )
   )
)

val enterpriseProvider = EnterpriseScannerProvider(
   backends = listOf(
      DataWedgeEnterpriseBackend(session = dataWedgeSession)
   )
)
```

Activity lifecycle pattern:

```kotlin
override fun onStart() {
   super.onStart()
   enterpriseProvider.start { result -> handleScan(result) }
}

override fun onStop() {
   enterpriseProvider.stop()
   cameraProvider.stop()
   super.onStop()
}
```

> Note: If your app module is not linked yet, keep sessions nullable and inject real implementations from Android app code when integrating into your Activity/Service lifecycle.

#### iOS concrete adapters in this repo

`mobile/ios/ScanProvider.swift` now includes:

- `AVFoundationCameraBackend` (camera path adapter interface)
- `ExternalScannerBackend` (enterprise scanner callback payload adapter)
- `ZebraRfidBackend` (RFID adapter that consumes `RfidScanSession`)
- `parseExternalScannerPayload(...)` helper for normalizing vendor callback payloads

`mobile/ios/AVFoundationCameraSession.swift` provides `AVFoundationCameraSession` which:

- requests camera permission on first start
- decodes common barcode formats via `AVCaptureMetadataOutput`
- supports duplicate scan debounce
- cleans up capture inputs/outputs on `stop()`

`mobile/ios/ExternalScannerSession.swift` provides `NotificationExternalScannerSession` which:

- subscribes to a named `NotificationCenter` event (`AssetraExternalScan` by default)
- converts callback payloads to `[String: String]`
- de-registers observer in `stop()` to avoid duplicate callbacks/leaks

iOS wiring pattern:

```swift
let session = NotificationExternalScannerSession()

let provider = EnterpriseScannerProvider(
   backends: [
      ExternalScannerBackend(session: session)
   ]
)

provider.start { result in
   handleScan(result)
}

// On lifecycle stop:
provider.stop()
```

Quick verification without hardware (iOS sample):

1. Start **Enterprise Provider** in `SampleSyncView`.
2. Tap **Simulate Enterprise Scan**.
3. Confirm **Last scan** updates and a local scan event is queued.
4. Tap **Sync Pending Events** to push the captured simulated event.

iOS camera wiring pattern:

```swift
let cameraSession = AVFoundationCameraSession(
   previewContainerLayer: previewHost.layer,
   debounceMs: 1200,
   onPermissionDenied: { showCameraPermissionAlert() }
)

let cameraProvider = CameraScanProvider(
   backends: [
      AVFoundationCameraBackend(session: cameraSession)
   ]
)

cameraProvider.start { result in
   handleScan(result)
}

// On lifecycle stop:
cameraProvider.stop()
```

### iOS Zebra RFID framework integration

`mobile/ios/RfidSession.swift` includes a real Zebra SDK bridge behind `#if canImport(ZebraRfidSdkFramework)` and keeps a notification fallback for non-hardware testing.

SDK package location expected in this workspace:

- `mobile/android/vendor/Zebra/123RFID_iOS_ReleasePackage_1.1.94/SDK_Framework/FrameworkScannerAndRfidSDK/RFIDFramework/ZebraRfidSdkFramework.xcframework`

Xcode integration steps (real app target):

1. In Xcode, open your iOS app target settings.
2. Add `ZebraRfidSdkFramework.xcframework` to **Frameworks, Libraries, and Embedded Content**.
3. Set embed mode to **Embed & Sign**.
4. Ensure the app target links the framework for both device and simulator slices.

Runtime behavior implemented:

- `makeDefaultRfidSession()` returns `HybridRfidSession`.
- `HybridRfidSession` starts both:
   - `ZebraSdkRfidSession` (real reader callbacks)
   - `NotificationRfidSession` (manual simulation path)
- Zebra path subscribes to SDK events (`reader appearance`, `session established`, `read`, `session termination`), establishes a session to the first available reader, starts inventory, and emits EPC values into `ScanResult`.
- Notification simulation (`AssetraRfidScan`) remains enabled so **Simulate RFID Scan** in the sample continues to work without hardware.

Sample wiring in this repo:

- `mobile/ios/SampleSyncView.swift` uses `makeDefaultRfidSession()`.
- `RfidScanProvider` receives `ZebraRfidBackend(session: rfidSession)` and emits source type `rfid`.

Quick iOS RFID verification:

1. Launch sample and tap **Start RFID Provider**.
2. If Zebra reader is connected, scan a tag and confirm **Last scan** updates with EPC payload.
3. Without hardware, tap **Simulate RFID Scan** and confirm the same UI/data path updates.
4. Tap **Sync Pending Events** to verify queued RFID captures are posted to `/api/v1/sync/`.

### Full implementation sequence (recommended)

1. Wire camera backend first
   - Use `CameraXMlKitSession` with `MlKitCameraBackend` in `CameraScanProvider`.
   - Verify one successful camera decode creates a pending local scan event.

2. Validate sync path from captured events
   - Run sync without seeding synthetic events (`SampleAppRunner.runSyncOnly`).
   - Confirm captured event is accepted by `POST /api/v1/sync/`.

3. Enable enterprise scanner backend
   - Add `DataWedgeBroadcastSession` to `DataWedgeEnterpriseBackend`.
   - Confirm DataWedge payload parses into normalized `ScanResult`.

4. Confirm lifecycle safety
   - Start provider in UI action or `onStart`.
   - Stop provider in `onStop` to avoid leaked camera/receiver resources.

5. Roll out hardware-specific optimizations
   - Tune backend order by device profile.
   - Add OEM-specific adapters behind `ScannerBackend` without changing sync contracts.

### Android dependencies for CameraX + ML Kit

Add these to your Android app module before using `CameraXBarcodeSession`:

```gradle
implementation "androidx.camera:camera-core:1.3.4"
implementation "androidx.camera:camera-camera2:1.3.4"
implementation "androidx.camera:camera-lifecycle:1.3.4"
implementation "androidx.camera:camera-view:1.3.4"
implementation "com.google.mlkit:barcode-scanning:17.2.0"
```

Also include camera permission in AndroidManifest:

```xml
<uses-permission android:name="android.permission.CAMERA" />
```

### Android dependencies for Zebra RFID API3

When integrating `ZebraRfidSession` in your Android app module, include the Zebra AARs from the checked-in SDK folder.

Example (`app/build.gradle`):

```gradle
repositories {
   flatDir {
      dirs "$rootDir/mobile/android/vendor/Zebra/RFIDAPI3_SDK_2.0.5.238"
   }
}

dependencies {
   implementation(name: "API3_ASCII-release-2.0.5.238", ext: "aar")
   implementation(name: "API3_CMN-release-2.0.5.238", ext: "aar")
   implementation(name: "API3_INTERFACE-release-2.0.5.238", ext: "aar")
   implementation(name: "API3_LLRP-release-2.0.5.238", ext: "aar")
   implementation(name: "API3_NGE-Transportrelease-2.0.5.238", ext: "aar")
   implementation(name: "API3_NGE-protocolrelease-2.0.5.238", ext: "aar")
   implementation(name: "API3_NGEUSB-Transportrelease-2.0.5.238", ext: "aar")
   implementation(name: "API3_READER-release-2.0.5.238", ext: "aar")
   implementation(name: "API3_TRANSPORT-release-2.0.5.238", ext: "aar")
   implementation(name: "rfidhostlib", ext: "aar")
   implementation(name: "rfidseriallib", ext: "aar")
}
```

Required Android permissions (minimum):

```xml
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
```

> Note: This repository contains mobile reference sources only and does not include the app module `build.gradle`; apply the snippet in your real Android app project.

### DataWedge setup and verification (Android)

Use this baseline profile on Zebra/enterprise devices:

1. Create a DataWedge profile and bind it to your app package/activity.
2. Enable **Intent Output**.
3. Set **Intent action** to `com.symbol.datawedge.api.RESULT_ACTION`.
4. Set **Intent category** to `android.intent.category.DEFAULT`.
5. Ensure scanned data and label type are included in extras.

Expected extras consumed by the sample:
- `com.symbol.datawedge.data_string` (or `data_string`)
- `com.symbol.datawedge.label_type` (or `label_type`)

Quick verification in sample UI (`SampleActivity`):
- Start **Enterprise Provider**.
- Confirm status shows `Provider: enterprise`.
- Scan a barcode and confirm **Last scan** updates.
- Press **Sync Pending Events** and confirm sync success toast.

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
