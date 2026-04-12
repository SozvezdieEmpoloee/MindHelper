import pytest

from apps.accounts.models import UserAccount
from apps.platform_ops.models import NeuralModelVersion


@pytest.fixture
def admin_user(db):
    return UserAccount.objects.create_superuser(
        email="admin@example.com",
        password="StrongPass123",
        display_name="Admin",
    )


@pytest.fixture
def regular_user(db):
    return UserAccount.objects.create_user(
        email="user@example.com",
        password="StrongPass123",
        display_name="User",
    )


@pytest.fixture
def model_version(db, admin_user):
    return NeuralModelVersion.objects.create(
        version_tag="v-test-1",
        model_name="MindSupport-Test",
        provider="local",
        safety_profile="strict",
        is_active=False,
        created_by_admin_user=admin_user,
    )

