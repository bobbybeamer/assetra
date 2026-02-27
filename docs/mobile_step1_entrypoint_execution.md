# Step 1 Execution: Production Entrypoint Wiring (Android + iOS)

This workspace does not include the real Android app module manifest or iOS app target root file, so apply the following in the **actual app repositories**.

## Android (real app module)

### File to edit

- `app/src/main/AndroidManifest.xml`

### Required result

- Launcher points to `com.assetra.sample.ProductionHomeComposeActivity`.
- Supporting screens remain registered without launcher intent filters.

### Patch snippet

```xml
<!-- Launcher activity -->
<activity
    android:name="com.assetra.sample.ProductionHomeComposeActivity"
    android:exported="true">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
    </intent-filter>
</activity>

<!-- Supporting activities (no launcher intent-filter) -->
<activity android:name="com.assetra.sample.ProductionScanComposeActivity" />
<activity android:name="com.assetra.sample.ProductionSyncStatusComposeActivity" />
<activity android:name="com.assetra.conflicts.ConflictResolutionComposeActivity" />
```

### Verification

1. Install debug build.
2. Launch app.
3. Confirm first screen is production home.
4. Confirm navigation opens scan and sync status screens.

## iOS (real app target)

### File to edit

- Main app target file (typically `YourAppNameApp.swift`).

### Required result

- App root uses `ProductionHomeView`.

### Patch snippet

```swift
import SwiftUI

@main
struct AssetraApp: App {
    var body: some Scene {
        WindowGroup {
            ProductionHomeView()
        }
    }
}
```

### Verification

1. Run on simulator/device.
2. Confirm root shows production home tabs.
3. Confirm `Scan` tab opens `ProductionScanView`.
4. Confirm `Sync` tab opens `ProductionSyncStatusView`.

## Execution record (fill during implementation)

### Android
- [ ] Manifest updated
- [ ] App launches into production home
- [ ] Scan route works
- [ ] Sync status route works

### iOS
- [ ] App root updated
- [ ] Tab shell launches correctly
- [ ] Scan tab route works
- [ ] Sync tab route works
