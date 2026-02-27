# Step 2 Execution: Dependencies + First Debug Build (Android + iOS)

Apply this in the real app repositories after completing step 1 entrypoint wiring.

## Android

### A) Verify required dependencies

1. Confirm CameraX + ML Kit dependencies exist in app module `build.gradle`:

```gradle
implementation "androidx.camera:camera-core:1.3.4"
implementation "androidx.camera:camera-camera2:1.3.4"
implementation "androidx.camera:camera-lifecycle:1.3.4"
implementation "androidx.camera:camera-view:1.3.4"
implementation "com.google.mlkit:barcode-scanning:17.2.0"
```

2. Confirm Zebra RFID AAR repo/dependencies are configured:

```gradle
repositories {
    flatDir {
        dirs "$rootDir/mobile/android/vendor/Zebra/RFIDAPI3_SDK_2.0.5.238"
    }
}

dependencies {
    implementation(name: "API3_ASCII-release-2.0.5.238", ext: "aar")
    implementation(name: "API3_CMN-release-2.0.5.238", ext: "aar")
    implementation(name: "API3_INTERFACE-release-2.0.5.238", ext: "aar")
    implementation(name: "API3_LLRP-release-2.0.5.238", ext: "aar")
    implementation(name: "API3_NGE-Transportrelease-2.0.5.238", ext: "aar")
    implementation(name: "API3_NGE-protocolrelease-2.0.5.238", ext: "aar")
    implementation(name: "API3_NGEUSB-Transportrelease-2.0.5.238", ext: "aar")
    implementation(name: "API3_READER-release-2.0.5.238", ext: "aar")
    implementation(name: "API3_TRANSPORT-release-2.0.5.238", ext: "aar")
    implementation(name: "rfidhostlib", ext: "aar")
    implementation(name: "rfidseriallib", ext: "aar")
}
```

3. Confirm manifest permissions include camera + bluetooth:

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
```

### B) Run first debug build

1. Clean + build debug:

```bash
./gradlew clean :app:assembleDebug
```

2. If build fails, triage in this order:
   - Manifest merge errors
   - Missing AAR / flatDir path errors
   - Compose/material/camerax dependency conflicts
   - Kotlin/AGP version compatibility

3. Install debug APK and verify app launches to production home.

### Android step-2 sign-off

- [ ] Dependencies are present and synced.
- [ ] `assembleDebug` succeeds.
- [ ] App launches and navigation shell appears.

## iOS

### A) Verify framework + target config

1. Add `ZebraRfidSdkFramework.xcframework` to target.
2. Set embed mode to **Embed & Sign**.
3. Confirm both slices are available in package:
   - `ios-arm64`
   - `ios-arm64_x86_64-simulator`

### B) Verify permissions/capabilities

1. Ensure camera usage description exists in Info.plist (`NSCameraUsageDescription`).
2. Ensure bluetooth usage description/capability required by your app target is configured for RFID path.

### C) Run first debug build

1. Build for simulator in Xcode (or `xcodebuild` with simulator destination).
2. Build for physical device.
3. Verify app launches into production home tabs.

4. If build fails, triage in this order:
   - Missing framework embedding/signing
   - Swift target membership/import visibility
   - Code signing/provisioning
   - Deployment target mismatch with SDK/framework

### iOS step-2 sign-off

- [ ] Framework linked and embedded correctly.
- [ ] Simulator build succeeds.
- [ ] Device build succeeds.
- [ ] Production home appears on launch.

## Completion output (record)

- Android build result: PASS / FAIL
- iOS simulator build result: PASS / FAIL
- iOS device build result: PASS / FAIL
- Blocking issues + owner:
