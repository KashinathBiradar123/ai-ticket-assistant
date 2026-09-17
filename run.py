import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "tickets.db"
ENV_PATH = BASE_DIR / ".env"


def check_env():
    if not ENV_PATH.exists():
        print("ERROR: .env file not found.")
        print("Copy .env.example to .env and add your GROQ_API_KEY.")
        sys.exit(1)
    print("[run] .env found")


def ensure_ingested():
    if DB_PATH.exists():
        print(f"[run] Database exists: {DB_PATH}")
        return
    print("[run] Database not found. Ingesting...")
    subprocess.run(
        [sys.executable, "-m", "app.ingest"],
        cwd=BASE_DIR,
        check=True,
    )


def start_services():
    print("[run] Starting FastAPI on port 8000...")
    fastapi = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
        ],
        cwd=BASE_DIR,
    )

    time.sleep(2)

    print("[run] Starting Streamlit on port 8501...")
    streamlit = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            "ui/streamlit_app.py",
            "--server.port", "8501",
        ],
        cwd=BASE_DIR,
    )

    print("")
    print("=" * 50)
    print("  AI Ticket Assistant is running")
    print("=" * 50)
    print("  API:  http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    print("  UI:   http://localhost:8501")
    print("=" * 50)
    print("")
    print("Press Ctrl+C to stop both servers.")
    print("")

    try:
        fastapi.wait()
        streamlit.wait()
    except KeyboardInterrupt:
        print("\n[run] Shutting down...")
        fastapi.terminate()
        streamlit.terminate()
        fastapi.wait()
        streamlit.wait()
        print("[run] Stopped.")


def main():
    print("[run] Starting AI Ticket Assistant...")
    check_env()
    ensure_ingested()
    start_services()


if __name__ == "__main__":
    main()