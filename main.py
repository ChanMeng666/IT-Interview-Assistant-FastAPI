import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router as api_router
from src.database.models import init_db
from src.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="IT Interview Assistant",
    description="An AI-powered technical interview assistant with code analysis capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to IT Interview Assistant API",
        "docs": "/docs",
        "gradio_ui": "http://localhost:7860"
    }

# Hello endpoint (for testing)
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# Register API routes
app.include_router(api_router, prefix="/api")

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    init_db()
    print("Database initialized successfully!")


if __name__ == "__main__":
    import uvicorn
    print("Starting IT Interview Assistant API...")
    print("API docs will be available at: http://localhost:8000/docs")
    print("Gradio UI will be available at: http://localhost:7860")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG_MODE
    )