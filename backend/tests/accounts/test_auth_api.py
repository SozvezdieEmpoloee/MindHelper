import pytest
from rest_framework.test import APIClient


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

