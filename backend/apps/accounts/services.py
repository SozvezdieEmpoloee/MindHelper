from .models import Role, UserAccount, UserRole


def assign_role_to_user(*, user: UserAccount, role_code: str) -> UserRole:
    role = Role.objects.get(code=role_code)
    user_role, _ = UserRole.objects.get_or_create(user=user, role=role)
    return user_role

