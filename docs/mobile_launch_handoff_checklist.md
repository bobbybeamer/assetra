# Mobile Launch Handoff Checklist

Use this checklist in the real mobile app repositories to complete launch wiring and device validation.

## 1) Android app-target wiring

### Launcher activity

In your real app `AndroidManifest.xml`, set the production home activity as launcher:

```xml
<activity
    android:name="com.assetra.sample.ProductionHomeComposeActivity"
    android:exported="true">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
    </intent-filter>
</activity>
```

### Keep supporting screens registered

Ensure these are registered (without launcher intent filters):

- `com.assetra.sample.ProductionScanComposeActivity`
- `com.assetra.sample.ProductionSyncStatusComposeActivity`
- `com.assetra.conflicts.ConflictResolutionComposeActivity`

### Android sign-off

- [ ] App launches into production home screen.
- [ ] "Open Scan" navigates to production scan screen.
- [ ] "Open Sync Status" navigates to production sync status screen.

## 2) iOS app-target wiring

### App root

Set production home as root view in your app target:

```swift
@main
struct AssetraApp: App {
   var body: some Scene {
      WindowGroup {
         ProductionHomeView()
      }
   }
}
```

### iOS sign-off

- [ ] App launches into tabbed production home.
- [ ] `Scan` tab opens `ProductionScanView`.
- [ ] `Sync` tab opens `ProductionSyncStatusView`.

## 3) Device E2E matrix (required)

Run on real devices for both platforms.

### Camera path

- [ ] Start camera provider.
- [ ] Scan valid barcode/QR.
- [ ] `Last scan` updates.
- [ ] Pending queue count increases.
- [ ] Stop scanner and reopen screen (no duplicate callbacks/leaks).

### Enterprise scanner path

- [ ] Start enterprise provider.
- [ ] Trigger enterprise scan (DataWedge / external callback).
- [ ] Captured value appears and enqueues correctly.

### RFID path

- [ ] Start RFID provider.
- [ ] Read RFID tag on connected reader.
- [ ] EPC payload captured and queued.
- [ ] If hardware unavailable, simulation path still works for smoke testing.

### Sync + conflicts

- [ ] Run `Retry Sync` from production sync status screen.
- [ ] Confirm `pending queue` decreases after successful sync.
- [ ] Seed/trigger a conflict and verify `Resolve Conflicts` button enables.
- [ ] Resolve via `Accept Server` and `Keep Local` paths.
- [ ] Verify post-resolution sync clears pending conflict acknowledgements.

## 4) Permission and lifecycle checks

### Android

- [ ] Camera permission denied path is user-safe and recoverable.
- [ ] Bluetooth permission prompts behave correctly for RFID reader usage.
- [ ] Background/foreground transitions do not leak scanner sessions.

### iOS

- [ ] Camera permission denied path is user-safe and recoverable.
- [ ] Bluetooth entitlement/permission behavior is validated for RFID sessions.
- [ ] Foreground/background transitions do not duplicate callbacks.

## 5) Release readiness decision

Mark release-ready only when all checkboxes are complete in the real app targets.
