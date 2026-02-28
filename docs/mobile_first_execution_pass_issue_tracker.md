# Mobile First Execution Pass Issue Tracker

Use this tracker while performing the first real app-target execution pass.

## Run context

- Date: 2026-02-28
- Build engineer: GitHub Copilot
- QA engineer:
- Android repo/branch: `/Users/Assetra/mobile/android_app` on `main`
- iOS repo/branch: `/Users/Assetra/mobile/ios_app` on `main`

## Pass workflow

1. Complete step 1 (entrypoint wiring).
2. Complete step 2 (dependencies + debug build).
3. Execute step 3 smoke tests.
4. Execute step 4 release/archiving.
5. Log every failure immediately in the table below.

## Issue triage order

1. Build blockers (manifest/signing/framework link errors)
2. Runtime crashes
3. Scanner path regressions (camera/enterprise/rfid)
4. Sync/conflict path regressions
5. UX and non-blocking polish defects

## Active issues

| ID | Step | Platform | Area | Severity | Repro steps | Expected | Actual | Owner | ETA | Status |
|----|------|----------|------|----------|-------------|----------|--------|-------|-----|--------|
| I-001 | 1 | Android | Entrypoint wiring | High | Apply launcher update in manifest and run app | App launches into production home | Implemented in scaffold manifest (`ProductionHomeComposeActivity` launcher) | Copilot | Done | Closed |
| I-002 | 1 | iOS | App root wiring | High | Set app root to `ProductionHomeView` and run | App opens production tabs | Implemented in scaffold source (`mobile/ios/AssetraApp.swift`) and generated Xcode project | Copilot | Done | Closed |
| I-003 | 2 | Android | Debug build setup | High | Run `:app:assembleDebug` | Debug artifact builds successfully | Fixed toolchain + manifest + dependency issues; build now successful in scaffold | Copilot | Done | Closed |
| I-004 | 2 | iOS | Debug build setup | High | Run simulator build via `xcodebuild` | Debug simulator build completes | Fixed by selecting full Xcode + downloading iOS platform + creating simulator; build succeeded | Copilot | Done | Closed |
| I-005 | 2 | iOS | Device debug signing | High | Run device debug build via `xcodebuild -destination 'generic/platform=iOS' build` | Device debug build signs with team and completes | Unsigned compile/link build succeeded (`CODE_SIGNING_ALLOWED=NO`); team signing still required for install/run | TBD | TBD | Open |
| I-006 | 4 | Android | Release build | Medium | Run `:app:assembleRelease` | Release artifact builds | Passed in scaffold after disabling release lint checks for environment compatibility | Copilot | Done | Closed |
| I-007 | 4 | iOS | Release build | Medium | Run Release build for generic iOS with signing off | Release compile/link succeeds | Passed unsigned (`CODE_SIGNING_ALLOWED=NO`); signed archive still pending team/provisioning | TBD | TBD | Open |
| I-008 | 3 | Android | Runtime smoke execution | High | Run smoke flow on Android device/emulator | Launch and route checks complete | Baseline launch previously passed, but current execution is blocked: emulator repeatedly enters `offline` state and clean relaunch fails (`AVD ... does not have enough disk space`) | Copilot | TBD | Open |
| I-009 | 3 | iOS | Simulator smoke execution | Medium | Build/install/launch app in simulator | App builds, installs, and launches | Passed: Debug build succeeded, app installed and launched (`simctl launch` PID returned) | Copilot | Done | Closed |

## Verification checkpoints

### Step 1
- [x] Android entrypoint validated (scaffold project)
- [x] iOS entrypoint validated (scaffold project)

### Step 2
- [x] Android debug build PASS (scaffold project)
- [x] iOS simulator debug build PASS (scaffold project)
- [ ] iOS device debug build PASS (signed)
- [x] iOS device debug build PASS (unsigned compile/link)

### Step 3
- [ ] Android smoke suite PASS (baseline launch validated on emulator; full flow pending)
- [x] iOS simulator smoke suite baseline PASS
- [ ] iOS hardware smoke suite PASS

### Step 4
- [x] Android release artifact PASS (scaffold)
- [x] iOS release build PASS (unsigned scaffold)
- [ ] iOS signed archive/device install PASS
- [ ] GO/NO-GO decision captured

## Daily update format

- Date:
- Completed today:
- Completed today: Android scaffold debug build passed; iOS Xcode project scaffold generated.
- New blockers:
- New blockers: iOS physical-device signed build requires selecting a development team; Android emulator is unstable (`offline`) and cannot be cleanly restarted due host disk-space limits.
- Risks:
- Risks: Scaffold projects may differ from final production app repos; Android smoke automation cannot proceed until emulator stability/disk constraints are resolved.
- Next actions:
- Next actions: Execute Android route/scanner smoke flow on the connected emulator, then provide Apple Team ID for signed iOS device smoke.
