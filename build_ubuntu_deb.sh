#!/usr/bin/env bash
set -euo pipefail

APP_NAME="People Counter"
BIN_NAME="PeopleCounter"
PKG_NAME="people-counter"
VERSION="1.0.0"

# 1) Build with PyInstaller
python -m PyInstaller --noconfirm --windowed --name "$BIN_NAME" \
  --add-data "assets/icon.png:assets" main.py

# 2) Stage Debian filesystem
STAGE="build/${PKG_NAME}_${VERSION}_amd64"
APP_DIR="${STAGE}/usr/local/${PKG_NAME}"
DESKTOP_DIR="${STAGE}/usr/share/applications"
DEBIAN_DIR="${STAGE}/DEBIAN"

mkdir -p "$APP_DIR" "$DESKTOP_DIR" "$DEBIAN_DIR"

# copy built app
cp -r "dist/${BIN_NAME}/." "$APP_DIR/"
chmod 0755 "${APP_DIR}/${BIN_NAME}"

# 3) .desktop launcher (menu entry)
cat > "${DESKTOP_DIR}/${PKG_NAME}.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Comment=People counting desktop app (Hikvision ISAPI)
Exec=/usr/local/${PKG_NAME}/${BIN_NAME}
Icon=${PKG_NAME}
Terminal=false
Categories=Utility;
StartupNotify=false
DESKTOP

# 4) Install icons into hicolor theme (multi-sizes)
SIZES=(16 24 32 48 64 128 256)
if [ -f assets/icon.png ]; then
  for s in "${SIZES[@]}"; do
    SZDIR="${STAGE}/usr/share/icons/hicolor/${s}x${s}/apps"
    mkdir -p "$SZDIR"
    convert assets/icon.png -resize ${s}x${s} "$SZDIR/${PKG_NAME}.png" 2>/dev/null || true
  done
fi

# 5) Control file (runtime deps for Qt)
cat > "${DEBIAN_DIR}/control" <<CONTROL
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: You <you@example.com>
Description: People counting desktop app (Hikvision ISAPI)
Depends: libxkbcommon-x11-0, libxcb-cursor0, libxcb-xinerama0, libegl1, libopengl0
CONTROL

# 6) Permissions
chmod -R 0755 "${STAGE}/usr" "${DEBIAN_DIR}"
chmod 0644 "${DESKTOP_DIR}/${PKG_NAME}.desktop" || true

# 7) Build .deb
OUT="${PKG_NAME}_${VERSION}_amd64.deb"
dpkg-deb --build "$STAGE" "$OUT"
echo
echo "Built: $OUT"
echo "Install with:  sudo apt install ./$(basename "$OUT")"
