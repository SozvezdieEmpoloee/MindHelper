from rest_framework.permissions import BasePermission


class IsAdminUserAccount(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)

