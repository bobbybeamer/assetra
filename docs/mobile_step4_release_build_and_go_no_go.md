# Step 4 Execution: Release Build + Go/No-Go (Android + iOS)

Run this after step 3 smoke tests pass (or all failures have approved mitigations).

## Android release build

### 1) Prepare release config

- Confirm release signing config is valid.
- Confirm minify/proguard settings are final for release variant.
- Confirm all required scanner/RFID classes are not stripped by R8 (add keep rules if required).

### 2) Build release artifact

Run in the real Android app project:

```bash
./gradlew :app:assembleRelease
```

Optional bundle build:

```bash
./gradlew :app:bundleRelease
```

### 3) Validate artifact

- Install release APK/AAB-based build on target device(s).
- Verify launch, scan routes, sync route, and conflict route still function.
- Verify no runtime crashes from minification/obfuscation.

### 4) Android release sign-off

- [ ] `assembleRelease` (and/or `bundleRelease`) passed
- [ ] Release artifact installed and launched
- [ ] Critical flows validated on release artifact

## iOS release archive

### 1) Prepare release config

- Confirm signing team/profile/certificates for release scheme.
- Confirm `ZebraRfidSdkFramework.xcframework` remains linked and Embed & Sign in release config.
- Confirm build settings are aligned for App Store / enterprise distribution target.

### 2) Create archive

In Xcode: Product -> Archive (Release scheme).

Or with CLI (example):

```bash
xcodebuild \
  -scheme <YourScheme> \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  archive
```

### 3) Validate archive

- Confirm archive completes without linker/signing errors.
- Export IPA (if applicable) for distribution channel.
- Install/test release build on physical device.

### 4) iOS release sign-off

- [ ] Release archive succeeded
- [ ] Export succeeded (if required)
- [ ] Release build validated on device

## Final go/no-go checklist

## Quality gate
- [ ] Android smoke tests: PASS
- [ ] iOS smoke tests: PASS
- [ ] No unresolved P0/P1 defects in scan/sync/conflict paths

## Security and permissions gate
- [ ] Camera permission flows validated
- [ ] Bluetooth permission/entitlement flows validated
- [ ] No unexpected crashes on denied permissions

## Release artifact gate
- [ ] Android release artifact validated
- [ ] iOS release archive/build validated

## Decision

- **GO** only if all gates above are checked.
- **NO-GO** if any P0 issues remain or release artifact validation fails.

## Step-4 output (record)

- Android release build result: PASS / FAIL
- iOS release archive result: PASS / FAIL
- Open issues blocking go-live:
- Final decision (GO / NO-GO):
- Approver + date:
