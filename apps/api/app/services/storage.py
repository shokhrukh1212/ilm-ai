from functools import lru_cache
from typing import Any, cast

from starlette.concurrency import run_in_threadpool
from supabase import Client, create_client

from ..settings import settings


class StorageService:
    def __init__(self, bucket: str | None = None) -> None:
        self.bucket = bucket or settings.supabase_storage_bucket
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        if self._client is None:
            if not settings.supabase_url or not settings.supabase_service_role_key:
                raise RuntimeError("Supabase storage credentials are not configured")
            self._client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        return self._client

    def _bucket(self) -> Any:
        return self.client.storage.from_(self.bucket)

    async def create_signed_upload_url(self, path: str) -> dict[str, str]:
        result = await run_in_threadpool(self._bucket().create_signed_upload_url, path)
        return cast(dict[str, str], result)

    async def create_signed_read_url(self, path: str, expires_in: int = 3600) -> str:
        result = await run_in_threadpool(self._bucket().create_signed_url, path, expires_in)
        data = cast(dict[str, Any], result)
        signed_url = data.get("signedURL") or data.get("signedUrl") or data.get("signed_url")
        if not isinstance(signed_url, str):
            raise RuntimeError("Supabase did not return a signed read URL")
        return signed_url

    async def upload_bytes(self, path: str, data: bytes, content_type: str) -> None:
        def _upload() -> None:
            self._bucket().upload(
                path,
                data,
                {
                    "content-type": content_type,
                    "x-upsert": "false",
                },
            )

        await run_in_threadpool(_upload)

    async def download_bytes(self, path: str) -> bytes:
        result = await run_in_threadpool(self._bucket().download, path)
        if isinstance(result, bytes):
            return result
        if hasattr(result, "read"):
            return cast(bytes, result.read())
        raise RuntimeError("Supabase did not return file bytes")

    async def remove(self, path: str) -> None:
        await run_in_threadpool(self._bucket().remove, [path])


@lru_cache
def get_storage_service() -> StorageService:
    return StorageService()
