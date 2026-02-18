# launcher.py
"""exe 入口：启动 Streamlit 并打开浏览器"""
import os
import sys
import threading
import time
import webbrowser

STREAMLIT_PORT = 8501
HOST = "127.0.0.1"

if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
    app_dir = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
    app_dir = base_path

app_path = os.path.join(base_path, "app.py")
if not os.path.exists(app_path):
    app_path = os.path.join(app_dir, "app.py")

os.chdir(app_dir)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
if base_path not in sys.path:
    sys.path.insert(0, base_path)


def open_browser():
    time.sleep(3)
    webbrowser.open(f"http://{HOST}:{STREAMLIT_PORT}")


if __name__ == "__main__":
    t = threading.Thread(target=open_browser, daemon=True)
    t.start()
    import streamlit.web.cli as stcli
    sys.argv = [
        "streamlit", "run", app_path,
        "--server.headless=true",
        f"--server.port={STREAMLIT_PORT}",
        f"--server.address={HOST}",
        "--global.developmentMode=false",
        "--browser.gatherUsageStats=false",
    ]
    stcli.main()
