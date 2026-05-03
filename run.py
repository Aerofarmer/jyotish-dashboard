import os
import sys
import time
import threading
import webbrowser
from app import create_app

app = create_app()

# ── Idle-shutdown config ───────────────────────────────────────────
IDLE_TIMEOUT   = int(os.getenv("IDLE_TIMEOUT",  1800))   # seconds (default 30 min)
WARN_BEFORE    = int(os.getenv("IDLE_WARN",      300))    # warn this many seconds before quit
CHECK_INTERVAL = 60                                        # how often the watcher polls

_last_activity = time.time()
_warned        = False


@app.before_request
def _touch_activity():
    global _last_activity, _warned
    _last_activity = time.time()
    _warned = False   # reset warning flag on any new request


def _notify(title: str, message: str):
    """Send a macOS notification if possible; always print to terminal."""
    print(f"\n  ⚠  {title}: {message}", flush=True)
    try:
        os.system(
            f'osascript -e \'display notification "{message}" '
            f'with title "{title}" sound name "Basso"\' 2>/dev/null'
        )
    except Exception:
        pass


def _idle_watcher():
    global _warned
    while True:
        time.sleep(CHECK_INTERVAL)
        idle = time.time() - _last_activity

        if idle >= IDLE_TIMEOUT:
            mins = IDLE_TIMEOUT // 60
            _notify(
                "Jyotish Dashboard",
                f"Shutting down after {mins} min of inactivity."
            )
            print(
                f"\n  ╔══════════════════════════════════════════╗"
                f"\n  ║  Auto-shutdown: {mins} min idle timeout reached  ║"
                f"\n  ║  Restart anytime with:  ./start.sh       ║"
                f"\n  ╚══════════════════════════════════════════╝\n",
                flush=True,
            )
            time.sleep(1)
            os._exit(0)

        elif not _warned and idle >= (IDLE_TIMEOUT - WARN_BEFORE):
            remaining = int((IDLE_TIMEOUT - idle) / 60)
            _notify(
                "Jyotish Dashboard",
                f"No activity for a while — will close in ~{remaining} min."
            )
            _warned = True


def open_browser():
    port = int(os.getenv("PORT", 5001))
    webbrowser.open(f"http://localhost:{port}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))

    idle_mins = IDLE_TIMEOUT // 60
    print(
        f"\n  Auto-shutdown: server will stop after "
        f"{idle_mins} min of no browser activity."
        f"\n  Override:  IDLE_TIMEOUT=3600 ./start.sh  (seconds)\n",
        flush=True,
    )

    # Start idle watcher as a background daemon
    t = threading.Thread(target=_idle_watcher, daemon=True)
    t.start()

    # Open browser after Flask is ready
    threading.Timer(1.5, open_browser).start()

    app.run(host="0.0.0.0", port=port, debug=False)
