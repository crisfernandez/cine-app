import os
import subprocess
import sys
import time

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
API_URL = "http://localhost:5000/api/salud"


def main():
    print("Arrancando API Flask (puerto 5000)...")
    api = subprocess.Popen([PYTHON, os.path.join(BASE_DIR, "app.py")], cwd=BASE_DIR)

    try:
        # Esperamos a que la API responda antes de lanzar la interfaz
        for _ in range(60):
            try:
                requests.get(API_URL, timeout=2)
                print("API Flask lista.")
                break
            except requests.RequestException:
                time.sleep(1)

        print("Arrancando interfaz Streamlit (puerto 8501)...")
        subprocess.run([
            PYTHON, "-m", "streamlit", "run", os.path.join(BASE_DIR, "interface.py"),
            "--server.port=8501", "--server.address=0.0.0.0"
        ])
    except KeyboardInterrupt:
        pass
    finally:
        api.terminate()


if __name__ == "__main__":
    main()
