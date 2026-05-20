import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.utils import timezone

from .managers import UserAccountManager


class UserAccount(AbstractBaseUser):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        BLOCKED = "blocked", "Blocked"
        DELETED = "deleted", "Deleted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255, db_column="password_hash")
    display_name = models.CharField(max_length=120)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    last_login = models.DateTimeField(null=True, blank=True, db_column="last_login_at")

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        db_table = "user_account"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.email

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE

    def has_perm(self, perm, obj=None) -> bool:
        return self.is_superuser or self.is_staff

    def has_module_perms(self, app_label) -> bool:
        return self.is_superuser or self.is_staff


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)

    class Meta:
        db_table = "role"
        ordering = ("code",)

    def __str__(self) -> str:
        return self.name


class UserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="role_links")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_links")
    assigned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_role"
        constraints = [
            models.UniqueConstraint(fields=("user", "role"), name="uq_user_role"),
        ]


class ChannelAccount(models.Model):
    class ChannelType(models.TextChoices):
        WEB = "web", "Web"
        TELEGRAM = "telegram", "Telegram"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name="channel_accounts")
    channel_type = models.CharField(max_length=32, choices=ChannelType.choices)
    external_user_id = models.CharField(max_length=255)
    external_chat_id = models.CharField(max_length=255, blank=True, null=True)
    bot_message_log = models.JSONField(default=list, blank=True)
    linked_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "channel_account"
        constraints = [
            models.UniqueConstraint(
                fields=("channel_type", "external_user_id"),
                name="uq_channel_external_user",
            ),
        ]
