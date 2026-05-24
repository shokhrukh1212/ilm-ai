from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import me
from .settings import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_base_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me.router)


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}
