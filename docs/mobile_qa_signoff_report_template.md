# Mobile QA Sign-Off Report Template

## Release Candidate

- Version / build:
- Date:
- QA owner:
- Platforms in scope: Android / iOS

## Step 1: Entrypoint wiring

### Android
- Launcher wired to production home: PASS / FAIL
- Supporting routes registered: PASS / FAIL
- Notes:

### iOS
- App root wired to `ProductionHomeView`: PASS / FAIL
- Production tabs/routes accessible: PASS / FAIL
- Notes:

## Step 2: Dependencies + debug build

### Android
- Dependencies verified: PASS / FAIL
- `assembleDebug` result: PASS / FAIL
- Launch check: PASS / FAIL
- Notes:

### iOS
- Framework integration verified: PASS / FAIL
- Simulator debug build: PASS / FAIL
- Device debug build: PASS / FAIL
- Launch check: PASS / FAIL
- Notes:

## Step 3: Device smoke tests

### Android smoke summary
- Camera path: PASS / FAIL
- Enterprise scanner path: PASS / FAIL
- RFID path: PASS / FAIL
- Sync + conflicts: PASS / FAIL
- Permission/lifecycle: PASS / FAIL
- Notes:

### iOS smoke summary
- Camera path: PASS / FAIL
- Enterprise scanner path: PASS / FAIL
- RFID path: PASS / FAIL
- Sync + conflicts: PASS / FAIL
- Permission/lifecycle: PASS / FAIL
- Notes:

## Step 4: Release build + go/no-go

### Android
- `assembleRelease`/`bundleRelease`: PASS / FAIL
- Release artifact install/run: PASS / FAIL
- Notes:

### iOS
- Release archive: PASS / FAIL
- Export/install (if applicable): PASS / FAIL
- Notes:

## Defects and risks

| ID | Platform | Severity | Summary | Owner | ETA | Status |
|----|----------|----------|---------|-------|-----|--------|
|    |          |          |         |       |     |        |

## Evidence references

- Test logs:
- Screenshots/video:
- Crash logs:
- Build artifacts:

## Final decision

- Android readiness: GO / NO-GO
- iOS readiness: GO / NO-GO
- Combined release decision: GO / NO-GO
- Approved by:
- Approval date:
