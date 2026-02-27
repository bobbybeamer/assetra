# Mobile Testing & Verification Guide

## Overview

This guide covers how to verify the iOS and Android mobile implementations are working end-to-end. Both platforms now support:

- **Camera-based barcode scanning** (QR, Code 128, Code 39, EAN, etc.)
- **Enterprise scanner callbacks** (DataWedge on Android, Notification-based on iOS)
- **Offline sync with conflict resolution** (keep_local replays as new events)
- **Comprehensive sample UIs** (SwiftUI on iOS, Jetpack Compose on Android)

## Architecture Overview

### Shared Components

Both platforms implement these core patterns:

1. **ScanProvider Interface**
   - Abstracts multiple scanner backends (camera, enterprise, RFID)
   - Automatic fallback if primary backend unavailable
   - iOS: `mobile/ios/ScanProvider.swift`
   - Android: `mobile/android/scan/ScanProviders.kt`

2. **LocalStore for Offline Queueing**
   - Stores pending scan events locally
   - Manages conflict acknowledgements
   - iOS: `mobile/ios/OfflineSyncSample.swift` (InMemoryLocalStore)
   - Android: `mobile/android/OfflineSyncSample.kt` (InMemoryLocalStore)

3. **Conflict Resolution with Keep-Local Requeue**
   - Resolving with `keep_local=false` creates a replay event
   - Replay event is synced on next `sync()` call
   - iOS: `mobile/ios/ConflictResolutionView.swift`
   - Android: `mobile/android/ConflictResolutionComposeActivity.kt`

## Platform-Specific Setup

### iOS Prerequisites

- Xcode 15+
- iOS 15+
- Camera permissions in Info.plist:
  ```xml
  <key>NSCameraUsageDescription</key>
  <string>Camera needed for barcode scanning</string>
  ```

### Android Prerequisites

- Android SDK API level 24+
- Camera permission in AndroidManifest.xml:
  ```xml
  <uses-permission android:name="android.permission.CAMERA" />
  <uses-feature android:name="android.hardware.camera" android:required="false" />
  ```
- Dependencies in build.gradle:
  ```gradle
  dependencies {
      implementation "androidx.camera:camera-camera2:1.3.0"
      implementation "androidx.camera:camera-lifecycle:1.3.0"
      implementation "androidx.camera:camera-view:1.3.0"
      implementation "com.google.mlkit:vision-barcode-scanning:17.2.0"
      implementation "androidx.compose.ui:ui:1.6.0"
      implementation "androidx.compose.material3:material3:1.1.0"
  }
  ```

## Testing Workflow

### Step 1: Start the Backend Server

```bash
cd /Users/Assetra
python manage.py migrate
python manage.py runserver
```

The server should be accessible at `http://127.0.0.1:8000`.

### Step 2: Run Smoke Tests (Backend Validation)

Verify the backend is ready:

```bash
python scripts/smoke_test.py \
  --base-url http://127.0.0.1:8000 \
  --username smoke_admin \
  --password SmokePass123! \
  --tenant-id 1
```

Expected output:
```json
{
  "ok": true,
  "report": [
    {"step": "auth", "status": 200},
    {"step": "asset_create", "status": 201},
    {"step": "scan_create", "status": 201},
    {"step": "sync", "status": 200},
    ...
  ]
}
```

### Step 3: Test iOS Mobile

#### Launch Sample App

1. Open the iOS project in Xcode
2. Register `SampleSyncView` as the entry point
3. Build and run on a simulator or device

#### Test Camera Scanning

1. Tap **"Start Camera Provider"** button
2. Point camera at a QR code or barcode
3. Verify:
   - Camera preview loads
   - Last scan updates with barcode value
   - Status shows "Scanner: camera active"

#### Test Enterprise Scanner (Simulator)

1. Tap **"Start Enterprise Provider"** button
2. Tap **"Simulate Enterprise Scan"** button
3. Verify:
   - **Last scan** updates with synthetic `ENT-XXXXX` value
   - **Status** shows "Captured: ENT-XXXXX"
   - Notification event posted successfully

#### Test Sync

1. Populate form with credentials:
   - **Base URL**: `http://YOUR_IP:8000` (or simulator hostname if running locally)
   - **Tenant ID**: `1`
   - **Username**: `smoke_admin`
   - **Password**: `SmokePass123!`
2. Tap **"Sync Pending Events"**
3. Verify:
   - Status updates to "Sync completed"
   - Any pending scan events are marked as synced

#### Test Conflict Resolution

1. Tap **"View Conflicts"** button
2. Verify conflict seeding appears (if no real conflicts exist)
3. Test **"Accept Server"**:
   - Conflict removed from list
   - Acknowledgement recorded
4. Test **"Keep Local"**:
   - Conflict removed from list
   - Replay event queued (visible in next sync)
   - Conflict acknowledgement recorded

### Step 4: Test Android Mobile

#### Launch Sample Activity

1. Import Android project into Android Studio
2. Register `SampleComposeActivity` as the entry point in AndroidManifest.xml
3. Build and run on emulator or device

#### Test Camera Scanning

1. Tap **"Start Camera Provider"** button
2. Grant camera permissions when prompted
3. Point camera at a QR code or barcode
4. Verify:
   - Camera preview loads
   - Last scan updates with barcode value
   - Status shows "Scanner: camera active"

#### Test Enterprise Scanner (Simulator)

1. Tap **"Start Enterprise Provider"** button
2. Tap **"Simulate Enterprise Scan"** button
3. Verify:
   - **Last scan** updates with synthetic `ENT-XXXXX` value
   - Toast shows "Captured: ENT-XXXXX"
   - Broadcast intent sent successfully

#### Test Sync

1. Populate form with credentials:
   - **Base URL**: `http://YOUR_IP:8000`
   - **Tenant ID**: `1`
   - **Username**: `smoke_admin`
   - **Password**: `SmokePass123!`
2. Tap **"Sync Pending Events"**
3. Verify:
   - Status updates to "Sync completed"
   - Any pending scan events are marked as synced

#### Test Conflict Resolution

1. Tap **"View Conflicts"** button
2. Verify conflict seeding appears
3. Test **"Accept Server"**:
   - Conflict card disappears
   - Acknowledgement recorded
4. Test **"Keep Local"**:
   - Conflict card disappears
   - Replay event queued
   - Acknowledgement recorded

## Acceptance Criteria

### iOS

- ✅ Camera scan creates pending local event
- ✅ Camera scan adds entry to local store
- ✅ Enterprise scan simulation works
- ✅ Sync completes without errors
- ✅ Conflict resolution view displays seeded conflicts
- ✅ Keep-local resolution queues replay event
- ✅ Accept-server resolution removes conflict
- ✅ No resource leaks on provider stop
- ✅ No duplicate callbacks after restart

### Android

- ✅ Camera provider with CameraX + ML Kit integration
- ✅ Camera scan creates pending local event
- ✅ Permission handling (request + denial gracefully)
- ✅ Enterprise scan via DataWedge simulation
- ✅ Sync completes without errors
- ✅ Conflict resolution view displays seeded conflicts
- ✅ Keep-local resolution queues replay event
- ✅ Accept-server resolution removes conflict
- ✅ No resource leaks on provider stop
- ✅ Compose UI fully functional

## Troubleshooting

### Camera Not Starting (iOS)

**Issue**: "Camera permission denied" alert appears.

**Solution**: 
1. Check Info.plist includes `NSCameraUsageDescription`
2. Grant camera permission in Settings > [App] > Camera
3. Restart app

### Camera Not Starting (Android)

**Issue**: "Camera permission denied" toast appears.

**Solution**:
1. Check AndroidManifest.xml includes `android.permission.CAMERA`
2. Grant camera permission via system prompt or Settings
3. Restart app

### Sync Fails with 401

**Issue**: Authentication error during sync.

**Solution**:
1. Verify credentials are correct
2. Verify base URL is reachable from device/simulator
3. Check network connectivity
4. Ensure user account exists on backend

### Conflicts Not Seeding

**Issue**: No conflicts appear in resolution view.

**Solution**:
1. Conflicts are only seeded if none exist
2. Restart app to trigger seeding on first load
3. Check InMemoryLocalStore.seedConflicts() is called

## Implementation Details

### Camera Session Lifecycle

**iOS**:
```swift
let session = AVFoundationCameraSession(...)
session.start { symbology, rawValue in
    // Handle decoded barcode
}
// Later:
session.stop()
```

**Android**:
```kotlin
val session = CameraXBarcodeSession(
    activity = this,
    previewView = previewView,
    debounceMs = 1200
)
session.start { symbology, rawValue ->
    // Handle decoded barcode
}
// Later:
session.stop()
```

### Scan Result Structure

Both platforms emit `ScanResult`:

```
symbology: String     // "qr_code", "code_128", etc.
rawValue: String      // The decoded barcode content
sourceType: String    // "camera" or "enterprise_scanner"
```

### Conflict Replay Payload

When keeping local value, a replay event is queued:

```
symbology: "conflict_replay"
rawValue: "asset=A-001;field=status;value=in_transit"
sourceType: "conflict_replay"
```

## Next Steps (P1 Features)

1. **RFID Backend Integration**
   - Both platforms have provider stubs (`RfidScanProvider`)
   - Awaiting RFID SDK selection

2. **Hardware-Specific Optimization**
   - Detect device profile from server
   - Adjust backend order based on available hardware
   - Cache capabilities locally

3. **Sync Scheduling**
   - Background sync on interval
   - Sync on app resume
   - Network change triggers

## Files Modified

### iOS
- `mobile/ios/ScanProvider.swift` - Enhanced with barcode format mapping
- `mobile/ios/AVFoundationCameraSession.swift` - Complete ML Kit integration
- `mobile/ios/OfflineSyncSample.swift` - Conflict replay implementation
- `mobile/ios/ConflictResolutionView.swift` - UI for conflict resolution
- `mobile/ios/SampleSyncView.swift` - Main sample UI

### Android
- `mobile/android/scan/CameraXBarcodeSession.kt` - CameraX + ML Kit implementation
- `mobile/android/scan/ScanProviders.kt` - Backend selection and fallback
- `mobile/android/OfflineSyncSample.kt` - Conflict replay implementation
- `mobile/android/SampleComposeActivity.kt` - New Compose-based main UI
- `mobile/android/ConflictResolutionComposeActivity.kt` - New Compose-based conflict UI

## Support & Debugging

Enable debug logging:

**iOS**:
```swift
NSLog("Scanning with %@", provider.name)
```

**Android**:
```kotlin
Log.d("Assetra", "Scanning with provider: ${provider.name}")
```

For detailed ML Kit barcode detection info:

**iOS**: Check `AVFoundationCameraSession` log output in Xcode console

**Android**: Check `CameraXBarcodeSession` with `adb logcat`
