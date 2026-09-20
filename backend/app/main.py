from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.auth import router as auth_router          # NEW
from app.api.emails import router as emails_router      # NEW

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)                          # NEW
app.include_router(emails_router)                        # NEW


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}