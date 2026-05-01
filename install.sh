#!/usr/bin/env bash
# ──────────────────────────────────────────────────────
#  Jyotish Dashboard — one-shot installer for Ubuntu/Linux
#  Creates a venv, installs deps, registers .desktop entry
#  Usage:  bash install.sh
# ──────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  Installing Jyotish Dashboard..."
echo ""

# Python 3.11+ check
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install it with: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  Created virtual environment."
fi

source .venv/bin/activate

# Upgrade pip silently
pip install --upgrade pip -q

# Install Python dependencies
echo "  Installing Python packages (this may take 2-3 minutes)..."
pip install -r requirements.txt -q

echo "  Dependencies installed."

# Copy .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env — edit it to add your API keys."
fi

# Make scripts executable
chmod +x start.sh

# ── Desktop entry ───────────────────────────────────
DESKTOP_FILE="$HOME/.local/share/applications/jyotish-dashboard.desktop"
ICON_PATH="$SCRIPT_DIR/app/static/img/icon.svg"

mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Jyotish Dashboard
GenericName=Vedic Astrology Software
Comment=Kundli, Panchang, Dasha & Transit charts
Exec=bash $SCRIPT_DIR/start.sh
Icon=$ICON_PATH
Terminal=false
Categories=Education;Science;
Keywords=astrology;kundli;vedic;panchang;dasha;
StartupNotify=true
StartupWMClass=jyotish-dashboard
EOF

# Mark as trusted (Ubuntu 22+)
if command -v gio &>/dev/null; then
    gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
fi

chmod +x "$DESKTOP_FILE"

# Update desktop database
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo ""
echo "  ✔  Installation complete!"
echo "  ✔  Desktop entry created: $DESKTOP_FILE"
echo ""
echo "  To launch:  ./start.sh"
echo "  Or search 'Jyotish' in your application menu."
echo ""
