import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.accounts.models import UserAccount


pytestmark = pytest.mark.django_db


def test_register_logs_user_in():
    client = APIClient()
    client.get("/api/v1/accounts/csrf/")

    response = client.post(
        "/api/v1/accounts/register/",
        {
            "email": "new-user@example.com",
            "display_name": "New User",
            "password": "StrongPass123",
        },
        format="json",
    )

    assert response.status_code == 201
    me_response = client.get("/api/v1/accounts/me/")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "new-user@example.com"


def test_login_and_logout_flow(regular_user):
    client = APIClient()
    client.get("/api/v1/accounts/csrf/")

    login_response = client.post(
        "/api/v1/accounts/login/",
        {
            "email": regular_user.email,
            "password": "StrongPass123",
        },
        format="json",
    )

    assert login_response.status_code == 200
    assert login_response.json()["email"] == regular_user.email

    me_response = client.get("/api/v1/accounts/me/")
    assert me_response.status_code == 200

    logout_response = client.post("/api/v1/accounts/logout/")
    assert logout_response.status_code == 204


def test_register_rejects_duplicate_email(regular_user):
    client = APIClient()
    client.get("/api/v1/accounts/csrf/")

    response = client.post(
        "/api/v1/accounts/register/",
        {
            "email": regular_user.email,
            "display_name": "Another User",
            "password": "StrongPass123",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "email" in response.json()


def test_register_rejects_duplicate_email_case_insensitive(regular_user):
    client = APIClient()
    client.get("/api/v1/accounts/csrf/")

    response = client.post(
        "/api/v1/accounts/register/",
        {
            "email": regular_user.email.upper(),
            "display_name": "Case User",
            "password": "StrongPass123",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["email"][0] == "Аккаунт с таким email уже существует."


def test_register_handles_integrity_error(monkeypatch):
    client = APIClient()
    client.get("/api/v1/accounts/csrf/")

    def raise_integrity_error(*args, **kwargs):
        raise IntegrityError("db failure")

    monkeypatch.setattr(UserAccount.objects, "create_user", raise_integrity_error)

    response = client.post(
        "/api/v1/accounts/register/",
        {
            "email": "broken@example.com",
            "display_name": "Broken User",
            "password": "StrongPass123",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Не удалось создать аккаунт. Проверьте введённые данные и попробуйте ещё раз."
