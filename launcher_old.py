# launcher.py
import os
import sys
import subprocess
import threading
import time
import webview
import requests
import chainlit as cl
import multiprocessing
from chainlit.config import config
from chainlit.cli import run_chainlit

def resource_path(relative_path):
    """
    Get the absolute path to a resource.
    Works for both development and when packaged by PyInstaller.
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller temporary folder
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def start_chainlit():
    # Mimic the --headless flag
    config.run.headless = True
    # Handle frozen state if needed
    if getattr(sys, "frozen", False):
        custom_build_path = os.path.join(sys._MEIPASS, "chainlit", "frontend", "dist")
        if os.path.exists(custom_build_path):
            config.ui.custom_build = custom_build_path
            print("Running frozen, custom_build folder found and set to:", config.ui.custom_build)
        else:
            print("Running frozen, but custom_build folder does NOT exist at:", custom_build_path)
    run_chainlit(resource_path("app_logic.py"))

def wait_for_server(url, timeout=10):
    """Poll the server until it responds with a status code 200, or until timeout."""
    start_time = time.time()
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Server is up!")
                return True
        except requests.exceptions.ConnectionError:
            # Server is not yet ready; continue polling.
            print("server not ready...")
            pass
        
        if time.time() - start_time > timeout:
            print("Timeout: Server did not start within {} seconds.".format(timeout))
            return False
        
        time.sleep(0.5)  # Wait a short time before trying again.


def main():
    # Start Chainlit in a separate process
    chainlit_process = multiprocessing.Process(target=start_chainlit)
    chainlit_process.start()
    print("Chainlit started in a separate process.")
    
    # Use the correct port; ensure it matches the port Chainlit is running on
    server_url = "http://localhost:8000"
    if wait_for_server(server_url):
        print("Creating window")
        webview.create_window("Authorship", server_url)
        print("Starting window")
        webview.start()
        print("Window started")
    else:
        print("Server did not start in time.")

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Necessary for frozen executables using multiprocessing on Windows
    main()