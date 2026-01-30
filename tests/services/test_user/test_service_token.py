from datetime import datetime, timedelta
from types import SimpleNamespace

from freezegun import freeze_time
from app.services.auth import create_access_token
from jose import jwt
import pytest

from tests.factories.users import user_factory


@freeze_time("2026-01-01 12:00:00")
def test_create_access_token_with_expires(monkeypatch, test_settings):
    monkeypatch.setattr("app.services.auth.settings", test_settings)

    token = create_access_token(
        {"sub": "email"},
        expires_delta=timedelta(minutes=30),
    )

    decoded = jwt.decode(
        token,
        test_settings.SECRET_KEY,
        algorithms=[test_settings.ALGORITHM],
    )

    assert decoded["sub"] == "email"
    assert decoded["exp"] == int(
        (datetime.utcnow() + timedelta(minutes=30)).timestamp()
    )


@freeze_time("2026-01-01 12:00:00")
def test_create_access_token_default_expires(monkeypatch, test_settings):
    monkeypatch.setattr("app.services.auth.settings", test_settings)

    token = create_access_token({"sub": "email"})

    decoded = jwt.decode(
        token,
        test_settings.SECRET_KEY,
        algorithms=[test_settings.ALGORITHM],
    )

    assert decoded["exp"] == int(
        (datetime.utcnow() + timedelta(minutes=15)).timestamp()
    )
    