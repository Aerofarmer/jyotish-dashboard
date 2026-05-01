#!/usr/bin/env bash
# ──────────────────────────────────────────────────────
#  Jyotish Dashboard — local launcher (non-Docker)
#  Usage:  ./start.sh
# ──────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Copy .env if not present
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "Created .env from .env.example — edit it to add API keys."
fi

# Set Swiss Ephemeris path
export SE_EPHE_PATH="$SCRIPT_DIR/ephe"

PORT=${PORT:-5000}
echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   🔮  Jyotish Vedic Dashboard         ║"
echo "  ║   http://localhost:$PORT               ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

python run.py
