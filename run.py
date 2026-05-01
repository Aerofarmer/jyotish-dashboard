import os
import webbrowser
import threading
from app import create_app

app = create_app()

def open_browser():
    port = int(os.getenv("PORT", 5000))
    webbrowser.open(f"http://localhost:{port}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    # Open browser after a short delay (let Flask start first)
    threading.Timer(1.5, open_browser).start()
    app.run(host="0.0.0.0", port=port, debug=False)
