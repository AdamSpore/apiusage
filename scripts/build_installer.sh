#!/usr/bin/env bash
set -euo pipefail

# Convenience wrapper to build the macOS app bundle and DMG installer in one step.
# Must be run on macOS.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CREATE_SCRIPT="$REPO_ROOT/scripts/create_mac_app.sh"
PACKAGE_SCRIPT="$REPO_ROOT/scripts/package_mac_app.sh"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This installer build must be run on macOS (Darwin)." >&2
  exit 1
fi

if [ ! -x "$CREATE_SCRIPT" ]; then
  echo "Missing executable $CREATE_SCRIPT" >&2
  exit 1
fi

if [ ! -x "$PACKAGE_SCRIPT" ]; then
  echo "Missing executable $PACKAGE_SCRIPT" >&2
  exit 1
fi

pushd "$REPO_ROOT" >/dev/null

"$CREATE_SCRIPT"
"$PACKAGE_SCRIPT"

echo "macOS app and DMG created in dist/. Drag UsageTracker.app from UsageTracker.dmg to Applications."

popd >/dev/null
