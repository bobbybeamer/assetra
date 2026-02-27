# Mobile First Execution Pass Issue Tracker

Use this tracker while performing the first real app-target execution pass.

## Run context

- Date:
- Build engineer:
- QA engineer:
- Android repo/branch:
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
| I-001 | 1 | Android | Entrypoint wiring | High | Apply launcher update in manifest and run app | App launches into production home | TBD | TBD | TBD | Open |
| I-002 | 1 | iOS | App root wiring | High | Set app root to `ProductionHomeView` and run | App opens production tabs | TBD | TBD | TBD | Open |

## Verification checkpoints

### Step 1
- [ ] Android entrypoint validated
- [ ] iOS entrypoint validated

### Step 2
- [ ] Android debug build PASS
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
- New blockers:
- Risks:
- Next actions:
