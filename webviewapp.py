import sys
import os
import subprocess
import threading
import time
import webview



def resource_path(relative_path):
    """
    Get absolute path to resource, works for development and when packaged with PyInstaller.
    """
    try:
        # When using PyInstaller, _MEIPASS stores the temporary folder path.
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def start_chainlit():
    """
    Launch the Chainlit server with the --headless flag so it doesn't open
    a browser window automatically.
    """
    print("running chainlit")
    # Use resource_path to get the correct path for app.py
    app_path = resource_path("basicapp.py")
    print("Using app.py at:", app_path)
    subprocess.Popen([sys.executable, "-m", "chainlit", "run", app_path, "--headless"])
if __name__ == "__main__":
    print("about to spin a thread to start chainlit")
    threading.Thread(target=start_chainlit, daemon=True).start()

    # Optionally, wait a short time to ensure the server starts.
    time.sleep(5)

    print("opening window")
    # Create and show a window loading the Chainlit app.
    webview.create_window("Authorship", "http://localhost:8000")
    webview.start()