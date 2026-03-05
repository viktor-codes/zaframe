"""
Юнит-тесты для app.services.auth с моками БД/UoW.
"""
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.uow import UnitOfWork
from app.models.user import User
from app.services import auth as auth_module
from app.services.auth import (
    get_current_user_from_token,
    logout_current_session,
)


@pytest.fixture
def mock_user():
    u = User(id=1, email="user@example.com", name="Test User")
    u.magic_link_token = None
    u.magic_link_expires_at = None
    return u


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_uow(mock_db):
    """UoW с мок-сессией (для logout тестов)."""
    uow = AsyncMock(spec=UnitOfWork)
    uow.session = mock_db
    uow.refresh_tokens = AsyncMock()
    return uow


class TestGetCurrentUserFromToken:
    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, mock_uow, mock_user):
        with patch.object(auth_module, "get_user_id_from_access_token", return_value=1):
            with patch.object(auth_module, "get_user_by_id", AsyncMock(return_value=mock_user)):
                user = await get_current_user_from_token(mock_uow, "valid-access-token")
        assert user is mock_user

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self, mock_uow):
        with patch.object(auth_module, "get_user_id_from_access_token", return_value=None):
            user = await get_current_user_from_token(mock_uow, "invalid")
        assert user is None

    @pytest.mark.asyncio
    async def test_user_not_found_returns_none(self, mock_uow):
        with patch.object(auth_module, "get_user_id_from_access_token", return_value=999):
            with patch.object(auth_module, "get_user_by_id", AsyncMock(return_value=None)):
                user = await get_current_user_from_token(mock_uow, "token")
        assert user is None


class TestLogoutCurrentSession:
    @pytest.mark.asyncio
    async def test_invalid_token_no_op(self, mock_uow, mock_user):
        with patch.object(auth_module, "parse_refresh_token", return_value=None):
            await logout_current_session(mock_uow, mock_user, "invalid")
        mock_uow.refresh_tokens.get_by_user_and_jti.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrong_user_token_no_op(self, mock_uow, mock_user):
        from app.core.security import RefreshTokenData
        from datetime import datetime, timezone
        data = RefreshTokenData(user_id=999, jti="jti", expires_at=datetime.now(timezone.utc))
        with patch.object(auth_module, "parse_refresh_token", return_value=data):
            await logout_current_session(mock_uow, mock_user, "token")
        mock_uow.refresh_tokens.get_by_user_and_jti.assert_not_called()
