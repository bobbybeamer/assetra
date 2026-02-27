# Mobile Next Sprint Checklist

## Current Status (2026-02-27)

- ✅ Android camera provider integration completed.
- ✅ iOS camera provider integration completed.
- ✅ Conflict keep-local requeue path completed on both platforms.
- ✅ Android enterprise scanner provider completed.
- ✅ iOS enterprise scanner provider completed.
- ✅ Android RFID provider integration completed (Zebra API3 path + fallback).
- ✅ iOS RFID provider integration completed (Zebra SDK bridge + fallback simulation).

## Next Action

Begin UI implementation on top of the completed scan/sync foundations.

1. Build a minimal production scan screen (Android + iOS)
   - Show scanner state, active provider, and latest scan value.
   - Trigger capture through existing provider start/stop actions.
2. Build a minimal sync status screen (Android + iOS)
   - Show pending queue count, last sync status, and retry action.
3. Integrate conflict resolution entry point
   - Route to existing conflict views when pending conflicts exist.
4. Keep sample modules as reference only
   - Reuse existing provider/store logic without changing sync contracts.

## Sprint Goal
Ship production-ready scan ingestion on both platforms for the camera path, and close the offline conflict requeue gap.

## Priority Plan

### P0 (must ship this sprint)

1. Android camera provider integration (`CameraScanProvider`)
   - File: `mobile/android/scan/ScanProviders.kt`
   - Implement `start` with ML Kit or ZXing scanner callbacks.
   - Implement `stop` to release camera/session resources safely.
   - Map decoded results to `ScanResult(symbology, rawValue, sourceType = "camera")`.
   - Acceptance:
     - First successful scan appears in local queue.
     - Repeated scans do not leak camera resources after `stop`.
     - Failure/permission denial does not crash app.

2. iOS camera provider integration (`CameraScanProvider`)
   - File: `mobile/ios/ScanProvider.swift`
   - Implement `start` using AVFoundation + Vision (or AV capture metadata pipeline).
   - Implement `stop` to end capture session and release delegates.
   - Map decoded values to `ScanResult(symbology, rawValue, sourceType = "camera")`.
   - Acceptance:
     - Camera scan adds pending local event.
     - Session cleanly stops/restarts without duplicate callbacks.
     - Permission denial returns controlled UX path.

3. Conflict keep-local requeue path
   - Files: `mobile/android/OfflineSyncSample.kt`, `mobile/ios/OfflineSyncSample.swift`
   - In `resolveConflict(..., useServerValue: false)`, enqueue a local update operation so the choice is replayed on next sync.
   - Preserve existing conflict acknowledgement behavior.
   - Acceptance:
     - `keep_local` decision creates requeued operation.
     - Next `sync()` includes replayed operation + conflict acknowledgement.
     - Conflict removed from pending list after resolution.

### P1 (next sprint candidate if capacity remains)

4. Android enterprise scanner provider
   - File: `mobile/android/scan/ScanProviders.kt`
   - Implement intent/broadcast receiver flow for enterprise scanners.
   - Add lifecycle-safe subscribe/unsubscribe in `start`/`stop`.

5. iOS enterprise scanner provider
   - File: `mobile/ios/ScanProvider.swift`
   - Implement external scanner callback bridge (vendor SDK wrapper).
   - Ensure callback de-registration in `stop`.

### P2 (defer unless hardware SDK availability is confirmed)

6. Android RFID provider integration
   - File: `mobile/android/scan/ScanProviders.kt`
   - Integrate target RFID SDK, map EPC/tag reads into `ScanResult`.

7. iOS RFID provider integration
   - File: `mobile/ios/ScanProvider.swift`
   - Integrate selected RFID SDK and normalize tag payloads.

## Suggested Delivery Order
1. Android camera
2. iOS camera
3. Conflict requeue (Android + iOS)
4. Enterprise scanner adapters
5. RFID adapters

## Definition of Done for this Sprint
- Camera-based scanning works end-to-end on both platforms (capture -> local queue -> sync).
- Conflict `keep_local` path replays an update on next sync on both platforms.
- No TODOs remain in camera or conflict-requeue code paths.
- Demo flow runs using existing sample modules without manual code edits.
