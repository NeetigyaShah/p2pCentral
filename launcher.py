import subprocess
import sys
import os
import time
import signal

def start_server():
    server_dir = os.path.join(os.path.dirname(__file__), "server")
    return subprocess.Popen([sys.executable, "app.py"], cwd=server_dir)

def start_ngrok():
    return subprocess.Popen(["ngrok", "http", "5000"])

def start_gui():
    gui_dir = os.path.join(os.path.dirname(__file__), "gui")
    return subprocess.Popen([sys.executable, "main_window.py"], cwd=gui_dir)

if __name__ == "__main__":
    server_proc = start_server()
    time.sleep(2)  # Give server time to start
    ngrok_proc = start_ngrok()
    time.sleep(3)  # Give ngrok time to start
    gui_proc = start_gui()

    try:
        gui_proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in [gui_proc, ngrok_proc, server_proc]:
            if proc and proc.poll() is None:
                proc.terminate()
        print("All processes terminated.")