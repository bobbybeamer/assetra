# Mobile First Execution Pass Issue Tracker

Use this tracker while performing the first real app-target execution pass.

## Run context

- Date: 2026-02-27
- Build engineer: GitHub Copilot
- QA engineer:
- Android repo/branch: `/Users/Assetra/mobile/android_app` on `main`
- iOS repo/branch:

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
| I-002 | 1 | iOS | App root wiring | High | Set app root to `ProductionHomeView` and run | App opens production tabs | TBD | TBD | TBD | Open |
| I-003 | 2 | Android | Debug build setup | High | Run `:app:assembleDebug` | Debug artifact builds successfully | Fixed toolchain + manifest + dependency issues; build now successful in scaffold | Copilot | Done | Closed |

## Verification checkpoints

### Step 1
- [x] Android entrypoint validated (scaffold project)
- [ ] iOS entrypoint validated

### Step 2
- [x] Android debug build PASS (scaffold project)
- [ ] iOS simulator/device debug build PASS

### Step 3
- [ ] Android smoke suite PASS
- [ ] iOS smoke suite PASS

### Step 4
- [ ] Android release artifact PASS
- [ ] iOS release archive PASS
- [ ] GO/NO-GO decision captured

## Daily update format

- Date:
- Completed today:
- Completed today: Android scaffold entrypoint wiring applied and `:app:assembleDebug` passed.
- New blockers:
- New blockers: iOS build target/project still not present in this workspace.
- Risks:
- Risks: Android scaffold is not yet the final production app repo.
- Next actions:
- Next actions: Create/import real iOS app target and execute step-2 simulator/device builds.
