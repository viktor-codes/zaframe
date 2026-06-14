"""
Юнит-тесты для app.core.security: JWT, OTP, refresh token.
"""

from datetime import UTC, datetime
from unittest.mock import patch

from app.core.config import settings
from app.core.security import (
    RefreshTokenData,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp_code,
    get_otp_expires_at,
    get_user_id_from_access_token,
    get_user_id_from_refresh_token,
    hash_otp_code,
    parse_refresh_token,
    verify_otp_code,
)


class TestCreateAccessToken:
    def test_creates_valid_jwt(self):
        token = create_access_token(user_id=1, email="u@example.com")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_returns_sub_and_email(self):
        token = create_access_token(user_id=42, email="a@b.com")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["email"] == "a@b.com"
        assert payload.get("type") == "access"
        assert "exp" in payload
        assert "iat" in payload


class TestGetUserIdFromAccessToken:
    def test_valid_token_returns_user_id(self):
        token = create_access_token(user_id=7, email="x@y.com")
        assert get_user_id_from_access_token(token) == 7

    def test_wrong_type_returns_none(self):
        refresh = create_refresh_token(1)
        assert get_user_id_from_access_token(refresh) is None

    def test_invalid_token_returns_none(self):
        assert get_user_id_from_access_token("garbage") is None
        assert get_user_id_from_access_token("") is None
        assert get_user_id_from_access_token("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.x") is None


class TestCreateAndParseRefreshToken:
    def test_creates_valid_refresh_token(self):
        token = create_refresh_token(user_id=10)
        assert isinstance(token, str)
        data = parse_refresh_token(token)
        assert data is not None
        assert isinstance(data, RefreshTokenData)
        assert data.user_id == 10
        assert isinstance(data.jti, str)
        assert len(data.jti) > 0
        assert data.expires_at.tzinfo is not None

    def test_parse_refresh_token_access_token_returns_none(self):
        access = create_access_token(1, "a@b.com")
        assert parse_refresh_token(access) is None

    def test_parse_refresh_token_invalid_returns_none(self):
        assert parse_refresh_token("invalid") is None
        assert parse_refresh_token("") is None

    def test_get_user_id_from_refresh_token(self):
        token = create_refresh_token(99)
        assert get_user_id_from_refresh_token(token) == 99


class TestDecodeToken:
    def test_valid_access(self):
        token = create_access_token(1, "e@mail.com")
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "access"

    def test_valid_refresh(self):
        token = create_refresh_token(1)
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_invalid_returns_none(self):
        assert decode_token("x") is None
        assert decode_token("Bearer abc") is None


class TestHashOtpCode:
    def test_deterministic(self):
        assert hash_otp_code("482913") == hash_otp_code("482913")

    def test_different_codes_different_hashes(self):
        a = hash_otp_code("111111")
        b = hash_otp_code("222222")
        assert a != b
        assert len(a) == 64


class TestGenerateOtpCode:
    def test_length_matches_settings(self):
        code = generate_otp_code()
        assert len(code) == settings.OTP_LENGTH
        assert code.isdigit()


class TestVerifyOtpCode:
    def test_valid_code(self):
        code = "123456"
        assert verify_otp_code(code, hash_otp_code(code)) is True

    def test_invalid_code(self):
        assert verify_otp_code("000000", hash_otp_code("123456")) is False


class TestGetOtpExpiresAt:
    def test_uses_otp_expire_minutes(self):
        with patch("app.core.security._utcnow") as m:
            m.return_value = datetime(2025, 3, 5, 12, 0, 0, tzinfo=UTC)
            expires = get_otp_expires_at()
        delta_minutes = (expires - m.return_value).total_seconds() / 60
        assert delta_minutes == settings.OTP_EXPIRE_MINUTES
