# Android + iOS Build To-Do (Step-by-Step)

Use this in the real mobile app repositories to complete build wiring, compile successfully, and validate release readiness.

Step 1 implementation guide:
- `docs/mobile_step1_entrypoint_execution.md`

Step 2 implementation guide:
- `docs/mobile_step2_dependencies_and_debug_build.md`

Step 3 implementation guide:
- `docs/mobile_step3_device_smoke_tests.md`

Step 4 implementation guide:
- `docs/mobile_step4_release_build_and_go_no_go.md`

Execution accelerators:
- `docs/mobile_commands_quick_run_sheet.md`
- `docs/mobile_qa_signoff_report_template.md`

Execution tracking artifacts:
- `docs/mobile_qa_signoff_report_prefilled_2026-02-27.md`
- `docs/mobile_first_execution_pass_issue_tracker.md`

Deferred credentials/inputs note:
- `docs/mobile_pending_inputs.md`

## Android build to-do

1. Confirm project entry wiring
   - Set launcher activity to `ProductionHomeComposeActivity` in `AndroidManifest.xml`.
   - Keep `ProductionScanComposeActivity`, `ProductionSyncStatusComposeActivity`, and conflict activity registered.

2. Verify dependencies in app module
   - CameraX + ML Kit dependencies are present.
   - Zebra RFID AAR repository/dependencies are configured in app Gradle.
   - Bluetooth and camera permissions are declared in manifest.

3. Configure scanner runtime behavior
   - Confirm DataWedge action/category mapping matches enterprise profile.
   - Confirm RFID SDK files are packaged in the app build.

4. Build debug variant
   - Run Gradle assemble for debug in the real Android app project.
   - Resolve compile/resource/manifest merge errors.

5. Install and run on device
   - Launch app into production home.
   - Navigate to Scan and Sync Status screens.

6. Execute device smoke tests
   - Camera scan capture works and queue increments.
   - Enterprise scanner capture path works.
   - RFID capture works on supported hardware.

7. Execute sync + conflict smoke tests
   - Retry Sync succeeds with valid credentials.
   - Resolve Conflicts button enables when conflicts exist.
   - Both conflict resolution actions clear pending conflicts after sync.

8. Validate lifecycle and permissions
   - Camera denied path is recoverable.
   - Bluetooth prompts/permissions behave correctly.
   - Foreground/background transitions do not duplicate callbacks.

9. Build release variant
   - Run release build in CI/local with signing config.
   - Confirm no proguard/r8 regressions for scanner and RFID paths.

10. Android sign-off
   - Mark Android ready only when debug + release builds and E2E checks all pass.

## iOS build to-do

1. Confirm app root wiring
   - Set app root to `ProductionHomeView` in `@main` app target.

2. Verify framework integration
   - Add `ZebraRfidSdkFramework.xcframework` to target.
   - Ensure framework is set to Embed & Sign.
   - Confirm device + simulator slices are available.

3. Verify capabilities and permissions
   - Confirm camera usage description in Info.plist.
   - Confirm Bluetooth usage descriptions/capabilities for RFID path.

4. Build for simulator
   - Build app target for simulator to validate SwiftUI/navigation integration.

5. Build for physical device
   - Build and run on a real device for camera + Bluetooth/RFID behavior.

6. Execute device smoke tests
   - App launches into production home tabs.
   - Scan tab: camera/enterprise/rfid actions update last scan and queue.
   - Sync tab: refresh/retry sync and conflict routing behave as expected.

7. Execute conflict + sync checks
   - Trigger conflict and confirm Resolve Conflicts path.
   - Validate both Accept Server and Keep Local outcomes.
   - Confirm follow-up sync clears pending conflict acknowledgements.

8. Validate lifecycle and permissions
   - Camera denied path is recoverable.
   - Bluetooth permission behavior is stable.
   - Foreground/background transitions do not duplicate scanner callbacks.

9. Archive/release build check
   - Create archive for release config.
   - Ensure no linker/signing issues with Zebra framework integration.

10. iOS sign-off
   - Mark iOS ready only when simulator + device + archive checks pass.

## Final combined release gate

- [ ] Android debug + release builds pass.
- [ ] iOS simulator + device + archive builds pass.
- [ ] Camera, enterprise scanner, and RFID E2E checks pass on target hardware.
- [ ] Sync/conflict flows pass on both platforms.
- [ ] Permission/lifecycle regressions are cleared.
- [ ] Product owner sign-off recorded.
