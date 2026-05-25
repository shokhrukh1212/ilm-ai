from typing import Any

import asyncpg

from .settings import settings


def database_url() -> str:
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def connect() -> Any:
    return await asyncpg.connect(database_url())
