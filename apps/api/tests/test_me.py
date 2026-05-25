from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth import get_current_user_id

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_ROW: dict[str, Any] = {
    "id": TEST_USER_ID,
    "email": "test@example.com",
    "full_name": "Test User",
    "lang": "uz-latn",
    "tier": "free",
    "daily_token_budget": 50000,
    "onboarded_at": None,
    "created_at": "2026-01-01T00:00:00+00:00",
}


def override_user_id() -> str:
    return TEST_USER_ID


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user_id] = override_user_id
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_me_returns_user_row(client: TestClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [TEST_ROW]

    mock_get = AsyncMock(return_value=mock_response)

    with patch("app.routers.me.httpx.AsyncClient") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_instance.get = mock_get
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        response = client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer faketoken"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == TEST_USER_ID
    assert data["email"] == "test@example.com"


def test_me_returns_404_when_user_missing(client: TestClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

    with patch("app.routers.me.httpx.AsyncClient") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        response = client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer faketoken"},
        )

    assert response.status_code == 404
