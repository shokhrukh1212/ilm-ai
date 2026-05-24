from collections.abc import Generator

from .settings import Settings, settings


def get_settings() -> Generator[Settings, None, None]:
    yield settings
