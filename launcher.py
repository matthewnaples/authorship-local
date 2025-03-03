# launcher.py
import os
import sys
import subprocess
import threading
import time
import webview
import requests

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
    main()