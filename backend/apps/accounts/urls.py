from django.urls import path

from .views import (
    CsrfCookieAPIView,
    CurrentUserAPIView,
    LoginAPIView,
    LogoutAPIView,
    RegistrationAPIView,
    UserDashboardStatsAPIView,
)


urlpatterns = [
    path("csrf/", CsrfCookieAPIView.as_view(), name="account-csrf"),
    path("register/", RegistrationAPIView.as_view(), name="account-register"),
    path("login/", LoginAPIView.as_view(), name="account-login"),
    path("logout/", LogoutAPIView.as_view(), name="account-logout"),
    path("me/", CurrentUserAPIView.as_view(), name="account-me"),
    path("me/stats/", UserDashboardStatsAPIView.as_view(), name="account-me-stats"),
]
