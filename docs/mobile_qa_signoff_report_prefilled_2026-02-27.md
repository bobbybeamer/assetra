# Mobile QA Sign-Off Report (Prefilled)

## Release Candidate

- Version / build: Reference workspace state @ commit `20c647d` and later doc updates
- Date: 2026-02-27
- QA owner: TBD
- Platforms in scope: Android / iOS

## Step 1: Entrypoint wiring

### Android
- Launcher wired to production home: PASS (scaffold app at `mobile/android_app`)
- Supporting routes registered: PASS (scaffold app at `mobile/android_app`)
- Notes: Implemented in scaffold project; still needs parity check when moved to final production app repo.

### iOS
- App root wired to `ProductionHomeView`: PASS (scaffold project)
- Production tabs/routes accessible: PENDING (build blocked before runtime verification)
- Notes: `mobile/ios/AssetraApp.swift` and `mobile/ios_app/AssetraIOSApp.xcodeproj` created; runtime verification pending.

## Step 2: Dependencies + debug build

### Android
- Dependencies verified: PASS (scaffold app)
- `assembleDebug` result: PASS (scaffold app)
- Launch check: PENDING (runtime install test not executed here)
- Notes: Build succeeded after Java/SDK configuration and Gradle fixes in scaffold app.

### iOS
- Framework integration verified: PARTIAL
- Simulator debug build: PASS (scaffold project)
- Device debug build: PARTIAL (unsigned build PASS; signed build pending)
- Launch check: PENDING
- Notes: Signed device build currently blocked by missing Development Team; unsigned device compile/link build succeeded using `CODE_SIGNING_ALLOWED=NO`.

## Step 3: Device smoke tests

### Android smoke summary
- Camera path: PENDING
- Enterprise scanner path: PENDING
- RFID path: PENDING
- Sync + conflicts: PENDING
- Permission/lifecycle: PENDING
- Notes: Requires physical hardware test pass.

### iOS smoke summary
- Camera path: PENDING
- Enterprise scanner path: PENDING
- RFID path: PENDING
- Sync + conflicts: PENDING
- Permission/lifecycle: PENDING
- Notes: Requires physical hardware test pass.

## Step 4: Release build + go/no-go

### Android
- `assembleRelease`/`bundleRelease`: PENDING
- Release artifact install/run: PENDING
- Notes: Execute in real app build pipeline.

### iOS
- Release archive: PENDING
- Export/install (if applicable): PENDING
- Notes: Execute in real app target with signing/provisioning.

## Defects and risks

| ID | Platform | Severity | Summary | Owner | ETA | Status |
|----|----------|----------|---------|-------|-----|--------|
| R-001 | Android+iOS | High | Entrypoint wiring pending in final production app targets (both scaffolded; final app repos still pending parity) | TBD | TBD | Open |
| R-002 | Android+iOS | High | Device E2E validation not completed on production hardware | TBD | TBD | Open |
| R-003 | Android+iOS | Medium | Release artifact validation not yet executed | TBD | TBD | Open |

## Evidence references

- Test logs: Pending
- Screenshots/video: Pending
- Crash logs: Pending
- Build artifacts: Pending

## Pending inputs to provide later

- Apple Development Team ID (for signed iOS device build and install)
- Provisioning profile / signing identity selection for `AssetraIOSApp` target

## Final decision

- Android readiness: NO-GO (pending real target wiring/build/tests)
- Android readiness: NO-GO (scaffold build passes, but real target runtime/release validation pending)
- iOS readiness: NO-GO (pending real target wiring/build/tests)
- Combined release decision: NO-GO
- Approved by: TBD
- Approval date: TBD

## Known completed foundation work (reference workspace)

- Scanner providers implemented for camera/enterprise/RFID on Android and iOS.
- Production scan, sync status, and conflict entry UI shells added.
- Launch handoff docs and step-by-step runbooks completed.
- Static diagnostics clean for workspace mobile sources.
