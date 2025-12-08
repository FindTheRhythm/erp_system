import pytest

from app import auth_service
from app.auth_service import AuthService


def test_validate_user_admin():
    role = AuthService.validate_user("admin", "admin")
    assert role == "admin"


def test_validate_user_viewer():
    role = AuthService.validate_user("viewer", "viewer")
    assert role == "viewer"


def test_validate_user_invalid():
    role = AuthService.validate_user("unknown", "wrong")
    assert role is None


def test_login_success(monkeypatch):
    published = []

    def fake_publish(event_type, data):
        published.append((event_type, data))

    monkeypatch.setattr(auth_service.rabbitmq_client, "publish_event", fake_publish)

    response = AuthService.login("admin", "admin")

    assert response.success is True
    assert response.role == "admin"
    assert published == [
        (
            "login",
            {
                "username": "admin",
                "role": "admin",
            },
        )
    ]


def test_login_failure(monkeypatch):
    published = []

    def fake_publish(event_type, data):
        published.append((event_type, data))

    monkeypatch.setattr(auth_service.rabbitmq_client, "publish_event", fake_publish)

    response = AuthService.login("bad", "creds")

    assert response.success is False
    assert response.role is None
    assert published == []


def test_logout(monkeypatch):
    published = []

    def fake_publish(event_type, data):
        published.append((event_type, data))

    monkeypatch.setattr(auth_service.rabbitmq_client, "publish_event", fake_publish)

    response = AuthService.logout("admin", "admin")

    assert response.success is True
    assert response.message == "Успешный выход"
    assert published == [
        (
            "logout",
            {
                "username": "admin",
                "role": "admin",
            },
        )
    ]

