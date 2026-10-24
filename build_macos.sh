#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
if [[ "$(uname -s)" != Darwin ]]; then
    echo "Build this app on macOS. PyInstaller cannot cross-compile macOS apps." >&2
    exit 1
fi

APP_PYTHON="${APP_PYTHON:-$PWD/.build-venv/bin/python}"
if [[ ! -x "$APP_PYTHON" ]]; then
    echo "Create .build-venv and install requirements-build.txt first (see README.md)." >&2
    exit 1
fi
export APP_VERSION="${APP_VERSION:-$(cat VERSION)}"
export APP_ARCH="${APP_ARCH:-$("$APP_PYTHON" -c 'import platform; print(platform.machine())')}"
if [[ ! "$APP_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "APP_VERSION must have the form 1.2.3." >&2
    exit 1
fi
if [[ "$APP_ARCH" != arm64 && "$APP_ARCH" != x86_64 ]]; then
    echo "APP_ARCH must be arm64 or x86_64. Build each architecture on a matching Mac." >&2
    exit 1
fi

"$APP_PYTHON" -c 'from PyInstaller.utils.hooks.tcl_tk import TclTkInfo; info = TclTkInfo(); print("Tkinter available:", info.available); raise SystemExit(0 if info.available else "Install Python from python.org with Tcl/Tk support.")'
"$APP_PYTHON" -m PyInstaller --noconfirm --clean packaging/macos.spec

APP_PATH="$PWD/dist/Easy CSV Cleaner.app"
/usr/bin/codesign --verify --deep --strict "$APP_PATH"
"$APP_PATH/Contents/MacOS/Easy CSV Cleaner" --smoke-test

ARCHIVE="dist/EasyCsvCleaner-${APP_VERSION}-macOS-${APP_ARCH}.zip"
# ditto preserves bundle symlinks, executable permissions and macOS metadata.
/usr/bin/ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ARCHIVE"
(cd dist && /usr/bin/shasum -a 256 "$(basename "$ARCHIVE")" > "$(basename "$ARCHIVE").sha256")
echo "Built: $ARCHIVE"
echo "Ad-hoc signed only; this build is not Apple notarized."
