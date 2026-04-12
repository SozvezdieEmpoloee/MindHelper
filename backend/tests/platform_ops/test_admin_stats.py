import pytest

from apps.chat.services import create_chat_message, get_or_create_user_chat
from apps.platform_ops.selectors import build_admin_dashboard_stats
from apps.platform_ops.services import activate_model_version


pytestmark = pytest.mark.django_db


def test_activate_model_version_makes_it_single_active(admin_user):
    first_version = admin_user.created_model_versions.create(
        version_tag="v1",
        model_name="MindSupport",
        provider="local",
        safety_profile="strict-v1",
        is_active=True,
    )
    second_version = admin_user.created_model_versions.create(
        version_tag="v2",
        model_name="MindSupport",
        provider="local",
        safety_profile="strict-v2",
        is_active=False,
    )

    activate_model_version(model_version=second_version)
    first_version.refresh_from_db()
    second_version.refresh_from_db()

    assert first_version.is_active is False
    assert second_version.is_active is True


def test_build_admin_dashboard_stats_returns_expected_shape(admin_user, regular_user, model_version):
    activate_model_version(model_version=model_version)
    chat = get_or_create_user_chat(user=regular_user, model_version=model_version)
    create_chat_message(chat=chat, sender_role="user", content_text="Hello")

    stats = build_admin_dashboard_stats()

    assert stats["users_total"] >= 2
    assert stats["messages_total"] >= 1
    assert stats["active_model"]["version_tag"] == "v-test-1"
