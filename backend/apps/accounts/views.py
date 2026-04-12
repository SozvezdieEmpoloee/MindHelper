from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, permissions, response, status, views

from .serializers import (
    UserLoginSerializer,
    UserAccountSerializer,
    UserDashboardStatsSerializer,
    UserRegistrationSerializer,
)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfCookieAPIView(views.APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def get(self, request):
        return response.Response({"detail": "CSRF cookie set."})


class RegistrationAPIView(views.APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return response.Response(UserAccountSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginAPIView(views.APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return response.Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            return response.Response(
                {"detail": "This account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)
        return response.Response(UserAccountSerializer(user).data)


class LogoutAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logout(request)
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserAccountSerializer(request.user)
        return response.Response(serializer.data)


class UserDashboardStatsAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserDashboardStatsSerializer.from_user(request.user)
        return response.Response(serializer.data)
