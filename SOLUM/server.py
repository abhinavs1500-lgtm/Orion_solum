#!/usr/bin/env python3
"""SOLUM Production Server (FastAPI + Google Maps 3D Platform)
Preserves all original launchers (start-windows.bat, start-mac.command, start-linux.sh).
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn
from backend.config import settings

def main():
    parser = argparse.ArgumentParser(description="SOLUM Server")
    parser.add_argument("--host", default=os.environ.get("HOST", settings.HOST), help="Host address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", settings.PORT)), help="Port number (default 8000)")
    parser.add_argument("--reload", action="store_true", default=False, help="Enable auto-reload for development")
    args = parser.parse_args()

    print(f"======================================================", flush=True)
    print(f"  SOLUM — One view. Every layer. A safer tomorrow.    ", flush=True)
    print(f"  Running on: http://{args.host}:{args.port}          ", flush=True)
    print(f"  Google Maps 3D: {'Configured' if settings.GOOGLE_MAPS_API_KEY else 'API key needed'}", flush=True)
    print(f"======================================================", flush=True)

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(ROOT),
        log_level="info"
    )

if __name__ == "__main__":
    main()
