# Mobile Commands Quick Run Sheet (Android + iOS)

Use this as the fast execution companion to steps 1–4.

## Android

## Build commands

```bash
# Debug build
./gradlew clean :app:assembleDebug

# Release APK
./gradlew :app:assembleRelease

# Release bundle (optional)
./gradlew :app:bundleRelease
```

## Optional diagnostics

```bash
# Dependency insight (example)
./gradlew :app:dependencies

# Install debug build (if using adb)
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## iOS

## Build/archive commands

```bash
# Simulator build (example)
xcodebuild \
  -scheme <YourScheme> \
  -configuration Debug \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  build

# Device release archive
xcodebuild \
  -scheme <YourScheme> \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  archive
```

## Notes

- Replace `<YourScheme>` with your app scheme.
- Ensure signing/provisioning and framework embedding are configured before archive.

## Manual verification checkpoints

- Launch into production home entrypoint.
- Verify Scan and Sync Status routes.
- Run device smoke tests from step 3.
- Complete final GO/NO-GO checks from step 4.

## Source docs

- `docs/mobile_step1_entrypoint_execution.md`
- `docs/mobile_step2_dependencies_and_debug_build.md`
- `docs/mobile_step3_device_smoke_tests.md`
- `docs/mobile_step4_release_build_and_go_no_go.md`
