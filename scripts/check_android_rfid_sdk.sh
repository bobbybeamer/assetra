#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK_DIR="$ROOT_DIR/mobile/android/vendor/Zebra/RFIDAPI3_SDK_2.0.5.238"

required_aars=(
  "API3_ASCII-release-2.0.5.238.aar"
  "API3_CMN-release-2.0.5.238.aar"
  "API3_INTERFACE-release-2.0.5.238.aar"
  "API3_LLRP-release-2.0.5.238.aar"
  "API3_NGE-Transportrelease-2.0.5.238.aar"
  "API3_NGE-protocolrelease-2.0.5.238.aar"
  "API3_NGEUSB-Transportrelease-2.0.5.238.aar"
  "API3_READER-release-2.0.5.238.aar"
  "API3_TRANSPORT-release-2.0.5.238.aar"
  "rfidhostlib.aar"
  "rfidseriallib.aar"
)

echo "[1/3] Checking Zebra SDK folder..."
if [[ ! -d "$SDK_DIR" ]]; then
  echo "❌ Missing SDK folder: $SDK_DIR"
  exit 1
fi

echo "[2/3] Checking required Zebra AAR files..."
missing=0
for aar in "${required_aars[@]}"; do
  if [[ -f "$SDK_DIR/$aar" ]]; then
    echo "✅ $aar"
  else
    echo "❌ $aar"
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo ""
  echo "Zebra SDK check failed: one or more AAR files are missing."
  exit 1
fi

echo "[3/3] Checking for Android app module build files in this workspace..."
if compgen -G "$ROOT_DIR/**/build.gradle" > /dev/null || compgen -G "$ROOT_DIR/**/build.gradle.kts" > /dev/null; then
  echo "⚠️ Gradle files detected, but this repository is a reference workspace."
else
  echo "ℹ️ No Android app module build files found in this workspace."
  echo ""
  echo "Next step in your Android app project:"
  echo "  1) apply from: \"\$rootDir/mobile/android/zebra_rfid_integration.gradle\""
  echo "  2) add Bluetooth permissions (BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN)"
  echo "  3) request BLUETOOTH_CONNECT + BLUETOOTH_SCAN at runtime on Android 12+"
fi

echo ""
echo "✅ Zebra RFID prerequisites check completed."
