from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from backend.config import settings
from backend.database import init_db
from backend.routers import system, issues, officials, land, chat, maps, simulation

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema and seed initial issues
    init_db()
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SOLUM — One view. Every layer. A safer tomorrow.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith((".js", ".css", ".html")) or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Include API Routers
app.include_router(system.router)
app.include_router(issues.router)
app.include_router(issues.complaints_router)
app.include_router(officials.router)
app.include_router(land.router)
app.include_router(chat.router)
app.include_router(maps.router)
app.include_router(simulation.router)

# Mount Uploads directory
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Mount Assets directory
assets_dir = settings.SOLUM_ROOT / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# Route root and HTML pages
HTML_PAGES = ["index.html", "prepare.html", "resolve.html", "officials.html", "report.html"]

@app.get("/")
async def serve_index():
    return FileResponse(settings.SOLUM_ROOT / "index.html")

@app.get("/{page_name}.html")
async def serve_page(page_name: str):
    file_path = settings.SOLUM_ROOT / f"{page_name}.html"
    if file_path.exists():
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"error": f"Page {page_name}.html not found"})

# Optional: serve docs or original template if requested
docs_dir = settings.SOLUM_ROOT / "docs"
if docs_dir.exists():
    app.mount("/docs", StaticFiles(directory=str(docs_dir)), name="docs")
