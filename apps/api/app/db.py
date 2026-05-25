from typing import Any

import asyncpg

from .settings import settings


def database_url() -> str:
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def connect() -> Any:
    # statement_cache_size=0 is required for Supabase Transaction pooler (port 6543)
    return await asyncpg.connect(database_url(), ssl="require", statement_cache_size=0)
