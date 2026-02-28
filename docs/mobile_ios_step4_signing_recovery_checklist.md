# iOS Step 4 Signing Recovery Checklist (5 Commands)

Run these after selecting your Apple Development Team and valid provisioning profile for `AssetraIOSApp`.

## 1) Confirm signing settings are present

```bash
xcodebuild \
  -project /Users/Assetra/mobile/ios_app/AssetraIOSApp.xcodeproj \
  -scheme AssetraIOSApp \
  -showBuildSettings | egrep 'DEVELOPMENT_TEAM|PRODUCT_BUNDLE_IDENTIFIER|CODE_SIGN_STYLE|PROVISIONING_PROFILE_SPECIFIER'
```

Expected: non-empty `DEVELOPMENT_TEAM` and valid signing/profile values.

## 2) Create Release archive (device)

```bash
xcodebuild \
  -project /Users/Assetra/mobile/ios_app/AssetraIOSApp.xcodeproj \
  -scheme AssetraIOSApp \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  -archivePath /Users/Assetra/mobile/ios_app/build/AssetraIOSApp.xcarchive \
  archive
```

Expected: `** ARCHIVE SUCCEEDED **`.

## 3) Export IPA from archive

```bash
xcodebuild -exportArchive \
  -archivePath /Users/Assetra/mobile/ios_app/build/AssetraIOSApp.xcarchive \
  -exportPath /Users/Assetra/mobile/ios_app/build/export \
  -exportOptionsPlist /Users/Assetra/mobile/ios_app/exportOptions.plist
```

Expected: exported IPA under `/Users/Assetra/mobile/ios_app/build/export`.

## 4) Install IPA/app to connected iPhone (manual via Xcode)

```bash
open -a Xcode /Users/Assetra/mobile/ios_app/build/AssetraIOSApp.xcarchive
```

Then use Organizer: Distribute App (or install using your normal internal path).

## 5) Validate release launch + critical routes on device

```bash
echo "On device verify: launch -> ProductionHomeView, Scan tab -> ProductionScanView, Sync tab -> ProductionSyncStatusView"
```

Record PASS/FAIL for each route in your sign-off notes.

## Final pass criteria

- Archive succeeds.
- Export succeeds.
- Release build installs on physical device.
- Home/Scan/Sync routes work on device.
