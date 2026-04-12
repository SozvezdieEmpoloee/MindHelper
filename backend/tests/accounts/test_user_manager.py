import pytest

from apps.accounts.models import UserAccount


pytestmark = pytest.mark.django_db


def test_create_user_hashes_password():
    user = UserAccount.objects.create_user(
        email="hash-test@example.com",
        password="StrongPass123",
        display_name="Hash Test",
    )

    assert user.password != "StrongPass123"
    assert user.check_password("StrongPass123")
    assert user.is_staff is False
    assert user.is_superuser is False


def test_create_superuser_sets_admin_flags():
    admin = UserAccount.objects.create_superuser(
        email="super@example.com",
        password="StrongPass123",
        display_name="Super User",
    )

    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.is_active is True

