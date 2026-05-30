from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import chat, gaps, materials, me, plan, quiz
from .settings import settings

app = FastAPI(title=settings.app_name)

_cors_origins = (
    ["*"]
    if settings.is_test_mode
    else [
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=not settings.is_test_mode,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me.router)
app.include_router(materials.router)
app.include_router(chat.router)
app.include_router(quiz.router)
app.include_router(gaps.router)
app.include_router(plan.router)


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}
