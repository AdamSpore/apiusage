#!/usr/bin/env bash
set -euo pipefail

APP_PATH="dist/UsageTracker.app"
DMG_PATH="dist/UsageTracker.dmg"
STAGING_DIR="dist/UsageTrackerDisk"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This packaging step can only run on macOS (Darwin)." >&2
  exit 1
fi

if [ ! -d "$APP_PATH" ]; then
  echo "App bundle not found at $APP_PATH. Run scripts/create_mac_app.sh first." >&2
  exit 1
fi

rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

cp -R "$APP_PATH" "$STAGING_DIR/"
if [ -f ./.env.example ]; then
  cp ./.env.example "$STAGING_DIR/.env.example"
fi

hdiutil create -volname "UsageTracker" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH"

echo "Created installer at $DMG_PATH"
