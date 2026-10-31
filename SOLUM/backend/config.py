import os
from pathlib import Path
from typing import List

# Paths
BACKEND_DIR = Path(__file__).resolve().parent
SOLUM_ROOT = BACKEND_DIR.parent
ENV_FILE = SOLUM_ROOT / ".env"

# Load simple .env if exists
if ENV_FILE.exists():
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

class Settings:
    PROJECT_NAME: str = "SOLUM"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SOLUM_ROOT: Path = SOLUM_ROOT
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Google Maps Platform
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyAOWcDHEha2UfkgMVCRou4YKTNLIswN8BE")
    
    # Database (supports persistent mounted storage on cloud hosts)
    DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", str(SOLUM_ROOT / "solum.db")))
    
    # File Storage (supports persistent uploads volume on cloud hosts)
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(SOLUM_ROOT / "uploads")))
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_MIME_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml",
        "video/mp4", "video/webm", "video/quicktime"
    ]
    
    # CORS
    _cors_env = os.getenv("CORS_ORIGINS", "*")
    if _cors_env.strip() == "*":
        CORS_ORIGINS: List[str] = ["*"]
    else:
        CORS_ORIGINS: List[str] = [
            origin.strip() for origin in _cors_env.split(",") if origin.strip()
        ]

    
    # Cache
    CACHE_DEFAULT_TTL: int = 600  # 10 minutes

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
