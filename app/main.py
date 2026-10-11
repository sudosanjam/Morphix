"""Morphix Local Web Application and Server Entrypoint."""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import config, setup_logging, VERSION, APP_NAME
from app.api.routes import router as api_router

logger = setup_logging()

WEB_DIR = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {APP_NAME} v{VERSION} local server...")
    # Clean up stale temporary files from previous sessions
    cleaned = config.clean_temp_files()
    if cleaned > 0:
        logger.info(f"Cleaned {cleaned} stale temporary files.")
    yield
    logger.info(f"Stopping {APP_NAME}...")


app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Universal Offline File Conversion, Optimization, and Processing Suite",
    lifespan=lifespan
)

# Strict localhost CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:*", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api")


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


# Static file serving
if (WEB_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(WEB_DIR / "css")), name="css")
if (WEB_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(WEB_DIR / "js")), name="js")
if (WEB_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html")
    return HTMLResponse("<h1>Morphix</h1><p>Web UI index not found.</p>", status_code=404)
