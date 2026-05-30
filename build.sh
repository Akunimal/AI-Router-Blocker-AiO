#!/bin/bash
# =====================================================================
#  Build script for Linux/macOS - AI Network Blocker
#  Requires: Python 3.x + PyInstaller (pip install pyinstaller)
# =====================================================================

echo ""
echo "============================================================"
echo "  AI Network Blocker - Build Script (Linux/macOS)"
echo "============================================================"
echo ""

# Check PyInstaller
if ! python3 -m PyInstaller --version > /dev/null 2>&1; then
    echo "[ERROR] PyInstaller is not installed."
    echo "Run: pip3 install pyinstaller"
    exit 1
fi

echo "[1/3] Cleaning previous builds..."
rm -rf dist build ai_blocker.spec

echo "[2/3] Compiling ai_blocker.py..."
echo ""

# Build options:
#   --onefile      -> Single portable binary
#   --windowed     -> No console window (GUI only via tkinter)
#   --name         -> Output binary name
#   --clean        -> Clean PyInstaller cache before building
#
# NOTE: --uac-admin is Windows-only and not used here.
#       On Linux/macOS, the app must be run with sudo.

python3 -m PyInstaller \
    --onefile \
    --windowed \
    --name "AI-Blocker" \
    --clean \
    ai_blocker.py

echo ""
if [ $? -ne 0 ]; then
    echo "[ERROR] Build failed. Check errors above."
    exit 1
fi

echo "[3/3] Copying binary to project root..."
cp -f dist/AI-Blocker ./AI-Blocker 2>/dev/null || cp -f "dist/AI-Blocker" "./AI-Blocker"

echo ""
echo "============================================================"
echo "  Build completed successfully!"
echo ""
echo "  Binary: ./AI-Blocker"
if [ -f "./AI-Blocker" ]; then
    echo "  Size: $(du -h ./AI-Blocker | cut -f1)"
fi
echo ""
echo "  NOTE: Run with sudo for hosts file access:"
echo "    sudo ./AI-Blocker"
echo "============================================================"
echo ""
