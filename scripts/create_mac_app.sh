#!/usr/bin/env bash
set -euo pipefail

# Build a minimal macOS app bundle that opens Terminal and runs usage_tracker.py
# from the repository root. The bundle ends up at dist/UsageTracker.app.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"
APP_NAME="UsageTracker"
APP_DIR="$DIST_DIR/${APP_NAME}.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

rm -rf "$APP_DIR"
mkdir -p "$MACOS_DIR" "$RESOURCES_DIR"

cat > "$MACOS_DIR/${APP_NAME}" <<'APP'
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$APP_DIR/../.." && pwd)"

PYTHON_BIN=$(command -v python3 || true)
if [ -z "$PYTHON_BIN" ]; then
  osascript -e 'display alert "Usage Tracker" message "python3 is required (install via Xcode Command Line Tools or python.org)."'
  exit 1
fi

GUI_SCRIPT="$REPO_ROOT/gui_usage_tracker.py"
if [ ! -f "$GUI_SCRIPT" ]; then
  osascript -e 'display alert "Usage Tracker" message "gui_usage_tracker.py not found. Keep the app next to the repository files."'
  exit 1
fi

if [ -f "$REPO_ROOT/.env" ]; then
  LOAD_ENV="set -a; source \"$REPO_ROOT/.env\"; set +a; "
else
  LOAD_ENV=""
fi

COMMAND="cd \"$REPO_ROOT\"; ${LOAD_ENV}\"$PYTHON_BIN\" \"$GUI_SCRIPT\" \"$@\""
ESCAPED_COMMAND=$(printf '%s' "$COMMAND" | sed 's/\\/\\\\/g; s/"/\\"/g')

osascript <<EOF
do shell script "$ESCAPED_COMMAND"
EOF
APP

chmod +x "$MACOS_DIR/${APP_NAME}"

cat > "$CONTENTS_DIR/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>UsageTracker</string>
    <key>CFBundleDisplayName</key>
    <string>Usage Tracker</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.usagetracker</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
PLIST

echo "Created $APP_DIR"
