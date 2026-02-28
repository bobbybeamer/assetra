# Mobile Pending Inputs (Can Be Provided Later)

This file lists external values/credentials not required for scaffold compile validation but required for signed iOS device/install flows.

## Required later

1. Apple Development Team ID
   - Used for iOS target signing in Xcode.

2. Provisioning selection
   - Automatic signing account or explicit provisioning profile for `AssetraIOSApp`.

## Where to apply when available

- Xcode -> Target `AssetraIOSApp` -> Signing & Capabilities
  - Team: `<YOUR_TEAM_ID>`
  - Signing: Automatic (or your selected profile)

## Commands to rerun after providing inputs

```bash
# Signed iOS device debug build
xcodebuild \
  -project mobile/ios_app/AssetraIOSApp.xcodeproj \
  -scheme AssetraIOSApp \
  -configuration Debug \
  -destination 'generic/platform=iOS' \
  build

# Signed iOS release archive
xcodebuild \
  -project mobile/ios_app/AssetraIOSApp.xcodeproj \
  -scheme AssetraIOSApp \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  archive
```
