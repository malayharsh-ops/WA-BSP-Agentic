from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import webhook_router, dashboard_router, campaigns_router, handoff_router

app = FastAPI(
    title="JSW ONE MSME WhatsApp Agent",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)
app.include_router(dashboard_router)
app.include_router(campaigns_router)
app.include_router(handoff_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
