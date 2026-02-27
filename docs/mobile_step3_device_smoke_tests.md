# Step 3 Execution: Device Smoke Tests (Android + iOS)

Run this after step 2 debug builds pass.

## Test setup

1. Use real devices for both platforms.
2. Ensure test account credentials are valid.
3. Ensure at least one test barcode/QR and one RFID tag are available.
4. Prepare enterprise scanner configuration (DataWedge / external scanner callback).

## Android smoke tests

### A) Launch + navigation

- [ ] App launches into production home.
- [ ] `Open Scan` opens production scan screen.
- [ ] `Open Sync Status` opens production sync status screen.

### B) Scan path checks

#### Camera
- [ ] Tap `Start Camera`.
- [ ] Scan a barcode/QR.
- [ ] `Last scan` updates.
- [ ] Pending queue increases.
- [ ] Tap `Stop Scanner`, then restart camera and confirm no duplicate callbacks.

#### Enterprise scanner
- [ ] Tap `Start Enterprise Scanner`.
- [ ] Trigger scan from enterprise scanner/DataWedge profile.
- [ ] Captured value appears in UI and queues locally.

#### RFID
- [ ] Tap `Start RFID`.
- [ ] Read an RFID tag with connected reader.
- [ ] EPC payload appears and queues locally.

### C) Sync + conflicts

- [ ] Open `Sync Status`.
- [ ] Tap `Refresh Status`, verify counts reflect scans.
- [ ] Tap `Retry Sync`, verify success.
- [ ] Confirm pending queue decreases after successful sync.
- [ ] Trigger/seed conflict and verify `Resolve Conflicts` button enables.
- [ ] Resolve conflict using `Accept Server`.
- [ ] Resolve conflict using `Keep Local`.
- [ ] Retry sync and verify conflict acknowledgements clear.

### D) Android lifecycle + permission checks

- [ ] Deny camera permission and confirm safe/recoverable UX.
- [ ] Validate bluetooth permissions flow for RFID usage.
- [ ] Foreground/background app while scanning; confirm no leaks/duplicate callbacks.

## iOS smoke tests

### A) Launch + navigation

- [ ] App launches into production home tabs.
- [ ] `Scan` tab opens production scan view.
- [ ] `Sync` tab opens production sync status view.

### B) Scan path checks

#### Camera
- [ ] Start camera provider.
- [ ] Scan barcode/QR and verify `Last scan` update.
- [ ] Confirm pending queue increases.
- [ ] Stop/start scanner and verify no duplicate callback behavior.

#### Enterprise scanner
- [ ] Start enterprise provider.
- [ ] Trigger external scanner callback path.
- [ ] Confirm captured value appears and queues locally.

#### RFID
- [ ] Start RFID provider.
- [ ] Read tag with Zebra reader and verify EPC capture.
- [ ] If hardware unavailable, run simulation smoke path and verify same queue update.

### C) Sync + conflicts

- [ ] Open `Sync` tab.
- [ ] Tap `Refresh Status`, verify queue/conflict counts.
- [ ] Tap `Retry Sync`, verify success.
- [ ] Trigger/seed conflict and verify `Resolve Conflicts` enables.
- [ ] Execute both `Accept Server` and `Keep Local` flows.
- [ ] Retry sync and verify conflict acknowledgements clear.

### D) iOS lifecycle + permission checks

- [ ] Deny camera permission and confirm recoverable UX.
- [ ] Validate bluetooth permission/capability behavior for RFID.
- [ ] Foreground/background transitions do not duplicate callbacks.

## Evidence capture template

Record one line per test run:

- Platform:
- Device model / OS version:
- Build variant:
- Feature tested:
- Result (PASS/FAIL):
- Notes / screenshot reference:
- Owner:
- Date:

## Step-3 sign-off

- [ ] Android smoke suite passed
- [ ] iOS smoke suite passed
- [ ] Failures (if any) filed with owners and ETA
