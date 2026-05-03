#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
#  Jyotish Vedic Dashboard — launcher
#  Usage:  ./start.sh
#          PORT=8080 ./start.sh      (custom port)
# ══════════════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [[ -f ".venv/bin/activate" ]]; then
    # shellcheck source=/dev/null
    source .venv/bin/activate
elif [[ -f "venv/bin/activate" ]]; then
    # shellcheck source=/dev/null
    source venv/bin/activate
else
    echo "  ✘  No virtual environment found. Run:  bash install.sh"
    exit 1
fi

# Create .env from example if missing
if [[ ! -f ".env" ]] && [[ -f ".env.example" ]]; then
    cp .env.example .env
    echo "  →  Created .env — run 'bash install.sh' to configure fully."
fi

# Load .env
if [[ -f ".env" ]]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' .env | grep -v '^$' | xargs) 2>/dev/null || true
fi

export SE_EPHE_PATH="$SCRIPT_DIR/ephe"
PORT="${PORT:-5001}"

echo ""
echo "  ╔════════════════════════════════════════════╗"
echo "  ║  🔮  Jyotish Vedic Dashboard               ║"
echo "  ║                                            ║"
echo "  ║  Open:   http://localhost:$PORT            ║"
echo "  ║  Stop:   Ctrl+C                            ║"
echo "  ╚════════════════════════════════════════════╝"
echo ""

python run.py
