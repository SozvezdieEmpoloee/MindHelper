from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAccountChangeForm, UserAccountCreationForm
from .models import ChannelAccount, Role, UserAccount, UserRole


@admin.register(UserAccount)
class UserAccountAdmin(BaseUserAdmin):
    add_form = UserAccountCreationForm
    form = UserAccountChangeForm
    filter_horizontal = ()
    list_display = (
        "email",
        "display_name",
        "status",
        "is_staff",
        "is_superuser",
        "created_at",
    )
    list_filter = ("status", "is_staff", "is_superuser")
    search_fields = ("email", "display_name")
    ordering = ("email",)
    readonly_fields = ("created_at", "last_login")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                    "display_name",
                    "status",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": ("is_staff", "is_superuser"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "last_login"),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "display_name",
                    "status",
                    "is_staff",
                    "is_superuser",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "assigned_at")
    list_filter = ("role",)


@admin.register(ChannelAccount)
class ChannelAccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "channel_type",
        "external_user_id",
        "external_chat_id",
        "is_active",
        "linked_at",
    )
    list_filter = ("channel_type", "is_active")
    search_fields = ("external_user_id", "external_chat_id", "user__email", "user__display_name")
    readonly_fields = ("linked_at",)
