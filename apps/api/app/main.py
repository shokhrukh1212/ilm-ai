from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import chat, materials, me
from .settings import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.app_base_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me.router)
app.include_router(materials.router)
app.include_router(chat.router)


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}
