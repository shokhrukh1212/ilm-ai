from fastapi import FastAPI

from .settings import settings

app = FastAPI(title=settings.app_name)


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}
