#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
#  Jyotish Vedic Dashboard — Interactive Installer
#  Works on macOS and Linux (Ubuntu / Debian / Fedora / Arch)
#  Usage:  bash install.sh
#          bash install.sh --update      (pull + reinstall, keep .env)
# ══════════════════════════════════════════════════════════════════
set -e

# ── Colours ───────────────────────────────────────────────────────
R='\033[0;31m' G='\033[0;32m' Y='\033[1;33m'
C='\033[0;36m' W='\033[1m' N='\033[0m'

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

UPDATE_MODE=false
[[ "${1:-}" == "--update" ]] && UPDATE_MODE=true

# ── Banner ────────────────────────────────────────────────────────
clear
echo ""
echo -e "${Y}  ╔══════════════════════════════════════════════╗${N}"
echo -e "${Y}  ║  🔮  Jyotish Vedic Dashboard — Installer    ║${N}"
echo -e "${Y}  ║      Free, local, open-source Jyotish       ║${N}"
echo -e "${Y}  ╚══════════════════════════════════════════════╝${N}"
echo ""

# ── Helpers ───────────────────────────────────────────────────────
ok()   { echo -e "  ${G}✔${N}  $*"; }
info() { echo -e "  ${C}→${N}  $*"; }
warn() { echo -e "  ${Y}!${N}  $*"; }
err()  { echo -e "  ${R}✘${N}  $*"; }
ask()  { echo -e "  ${W}?${N}  $*"; }

# ── Detect OS ─────────────────────────────────────────────────────
OS="linux"
[[ "$(uname)" == "Darwin" ]] && OS="macos"
ok "Detected OS: $OS"

# ── Step 1: Sync from Git ─────────────────────────────────────────
echo ""
echo -e "${W}[1/6] Git sync${N}"
if git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
    if $UPDATE_MODE; then
        info "Pulling latest changes from GitHub…"
        git pull origin main && ok "Up to date."
    else
        LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "")
        REMOTE=$(git ls-remote origin HEAD 2>/dev/null | awk '{print $1}' || echo "")
        if [[ -n "$REMOTE" && "$LOCAL" != "$REMOTE" ]]; then
            ask "Updates are available. Pull now? [Y/n]"
            read -r ans
            if [[ "${ans:-Y}" =~ ^[Yy]$ ]]; then
                git pull origin main && ok "Pulled latest changes."
            else
                warn "Skipped pull — running existing version."
            fi
        else
            ok "Already up to date."
        fi
    fi
else
    warn "Not a git repo — skipping sync. (Clone first for auto-updates)"
fi

# ── Step 2: Python check ──────────────────────────────────────────
echo ""
echo -e "${W}[2/6] Python${N}"
PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        if "$cmd" -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
            VER=$("$cmd" --version 2>&1)
            PYTHON="$cmd"
            ok "Found $cmd  ($VER)"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    err "Python 3.10+ not found."
    if [[ "$OS" == "macos" ]]; then
        echo "     Install with Homebrew:  brew install python"
        echo "     Or download from:       https://www.python.org/downloads/"
    else
        echo "     sudo apt install python3 python3-pip python3-venv   # Debian/Ubuntu"
        echo "     sudo dnf install python3                            # Fedora"
        echo "     sudo pacman -S python                               # Arch"
    fi
    exit 1
fi

# ── Step 3: Virtual environment + packages ────────────────────────
echo ""
echo -e "${W}[3/6] Virtual environment & packages${N}"
if [[ ! -d ".venv" ]]; then
    info "Creating virtual environment…"
    "$PYTHON" -m venv .venv
    ok "Created .venv"
else
    ok ".venv already exists."
fi

# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip -q
info "Installing Python packages (first run takes 2–4 min)…"
pip install -r requirements.txt -q
ok "All packages installed."

# ── Step 4: Swiss Ephemeris data files ────────────────────────────
echo ""
echo -e "${W}[4/6] Swiss Ephemeris data files${N}"
mkdir -p ephe
ALL_PRESENT=true
for f in seas_18.se1 semo_18.se1 sepl_18.se1; do
    if [[ ! -f "ephe/$f" ]]; then
        ALL_PRESENT=false
        info "Downloading $f (~10 MB)…"
        if command -v curl &>/dev/null; then
            curl -s "https://www.astro.com/ftp/swisseph/ephe/$f" -o "ephe/$f" \
                && ok "$f downloaded." \
                || { err "Failed: $f — check internet connection."; }
        elif command -v wget &>/dev/null; then
            wget -q "https://www.astro.com/ftp/swisseph/ephe/$f" -O "ephe/$f" \
                && ok "$f downloaded." \
                || { err "Failed: $f — check internet connection."; }
        else
            err "Neither curl nor wget found. Install one then re-run install.sh"
            exit 1
        fi
    fi
done
$ALL_PRESENT && ok "Ephemeris files already present."

# ── Step 5: Configuration (.env) ──────────────────────────────────
echo ""
echo -e "${W}[5/6] Configuration (.env)${N}"

if [[ -f ".env" ]] && ! $UPDATE_MODE; then
    ok ".env already exists — keeping your settings."
else
    cp .env.example .env

    # Auto-generate a secure Flask secret key
    SECRET=$("$PYTHON" -c "import secrets; print(secrets.token_hex(32))")
    if [[ "$OS" == "macos" ]]; then
        sed -i '' "s/change-me-to-random-string/$SECRET/" .env
    else
        sed -i "s/change-me-to-random-string/$SECRET/" .env
    fi
    ok "Generated FLASK_SECRET_KEY."

    echo ""
    echo -e "  ${W}AI-enhanced day notes${N} (optional)"
    echo "  Enriches iCal & Obsidian exports with 2-sentence Vedic insights."
    echo "  All astrology runs fully offline — AI is completely optional."
    echo ""
    echo "    1) Ollama  — local, free, private   (install once, runs on your machine)"
    echo "    2) Groq    — cloud, free tier, fast  (free key at console.groq.com)"
    echo "    3) OpenRouter — cloud, free models   (free key at openrouter.ai)"
    echo "    4) Skip    — no AI notes"
    echo ""
    ask "Pick [1-4]  (default: 4):"
    read -r LLM_CHOICE

    case "${LLM_CHOICE:-4}" in
    1)
        echo ""
        ask "Ollama model  [default: llama3.2]:"
        read -r OM
        OM="${OM:-llama3.2}"
        printf '\n# Open LLM — Ollama (local)\nLLM_BASE_URL=http://localhost:11434/v1\nLLM_API_KEY=ollama\nLLM_MODEL=%s\n' "$OM" >> .env
        ok "Configured Ollama ($OM)."
        if ! command -v ollama &>/dev/null; then
            warn "Ollama not found. Install from https://ollama.com then run:"
            warn "  ollama pull $OM"
        else
            info "Pulling $OM (may take a moment)…"
            ollama pull "$OM" 2>/dev/null && ok "Model ready." \
                || warn "Pull failed — run manually: ollama pull $OM"
        fi
        ;;
    2)
        echo ""
        ask "Groq API key (get free at console.groq.com):"
        read -r GK
        ask "Model  [default: llama-3.1-8b-instant]:"
        read -r GM
        GM="${GM:-llama-3.1-8b-instant}"
        printf '\n# Open LLM — Groq\nLLM_BASE_URL=https://api.groq.com/openai/v1\nLLM_API_KEY=%s\nLLM_MODEL=%s\n' "$GK" "$GM" >> .env
        ok "Configured Groq ($GM)."
        ;;
    3)
        echo ""
        ask "OpenRouter API key (get free at openrouter.ai):"
        read -r OK_KEY
        ask "Model  [default: meta-llama/llama-3.2-3b-instruct:free]:"
        read -r OM2
        OM2="${OM2:-meta-llama/llama-3.2-3b-instruct:free}"
        printf '\n# Open LLM — OpenRouter\nLLM_BASE_URL=https://openrouter.ai/api/v1\nLLM_API_KEY=%s\nLLM_MODEL=%s\n' "$OK_KEY" "$OM2" >> .env
        ok "Configured OpenRouter ($OM2)."
        ;;
    *)
        ok "AI notes skipped — app works fully offline without them."
        ;;
    esac
fi

# ── Step 6: Desktop shortcut ──────────────────────────────────────
echo ""
echo -e "${W}[6/6] Desktop shortcut${N}"

ICON_PATH="$REPO_DIR/app/static/img/icon.svg"

if [[ "$OS" == "macos" ]]; then
    echo ""
    echo "  Options:"
    echo "    1) Desktop .command file  (double-click to launch)"
    echo "    2) Skip"
    echo ""
    ask "Pick [1-2]  (default: 1):"
    read -r MAC_OPT

    if [[ "${MAC_OPT:-1}" == "1" ]]; then
        CMD_FILE="$HOME/Desktop/Jyotish Dashboard.command"
        cat > "$CMD_FILE" << CMDEOF
#!/usr/bin/env bash
# Jyotish Vedic Dashboard launcher
cd "$REPO_DIR"
source .venv/bin/activate
export SE_EPHE_PATH="$REPO_DIR/ephe"
python run.py
CMDEOF
        chmod +x "$CMD_FILE"
        ok "Created: ~/Desktop/Jyotish Dashboard.command"
        info "Double-click it anytime to open the dashboard."
        info "Tip: drag it to your Dock for a permanent one-click tile."
    else
        ok "Shortcut skipped."
    fi

else  # Linux
    echo ""
    echo "  Options:"
    echo "    1) App menu entry  (searchable in GNOME / KDE launcher)"
    echo "    2) App menu + Desktop icon"
    echo "    3) Skip"
    echo ""
    ask "Pick [1-3]  (default: 1):"
    read -r LNX_OPT

    ENTRY="[Desktop Entry]
Version=1.0
Type=Application
Name=Jyotish Dashboard
GenericName=Vedic Astrology Software
Comment=Kundli, Panchang, Dasha, Transit & Predictions
Exec=bash $REPO_DIR/start.sh
Icon=$ICON_PATH
Terminal=false
Categories=Education;Science;
Keywords=astrology;kundli;vedic;panchang;jyotish;
StartupNotify=true"

    if [[ "${LNX_OPT:-1}" =~ ^[12]$ ]]; then
        mkdir -p "$HOME/.local/share/applications"
        APP_FILE="$HOME/.local/share/applications/jyotish-dashboard.desktop"
        printf '%s\n' "$ENTRY" > "$APP_FILE"
        chmod +x "$APP_FILE"
        command -v gio &>/dev/null \
            && gio set "$APP_FILE" metadata::trusted true 2>/dev/null || true
        command -v update-desktop-database &>/dev/null \
            && update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
        ok "App menu entry created — search 'Jyotish' in your launcher."

        if [[ "${LNX_OPT}" == "2" ]]; then
            DESK_FILE="$HOME/Desktop/jyotish-dashboard.desktop"
            printf '%s\n' "$ENTRY" > "$DESK_FILE"
            chmod +x "$DESK_FILE"
            command -v gio &>/dev/null \
                && gio set "$DESK_FILE" metadata::trusted true 2>/dev/null || true
            ok "Desktop icon created."
        fi
    else
        ok "Shortcut skipped."
    fi
fi

chmod +x start.sh

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${Y}  ══════════════════════════════════════════════${N}"
echo -e "${G}  ✔  Installation complete!${N}"
echo -e "${Y}  ══════════════════════════════════════════════${N}"
echo ""
echo "  Start anytime:     ./start.sh"
echo "  Update anytime:    bash install.sh --update"
echo "  App URL:           http://localhost:5001"
echo ""
ask "Launch the dashboard now? [Y/n]"
read -r LAUNCH_NOW
if [[ "${LAUNCH_NOW:-Y}" =~ ^[Yy]$ ]]; then
    echo ""
    exec ./start.sh
fi
