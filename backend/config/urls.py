from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/chat/", include("apps.chat.urls")),
    path("api/v1/assessments/", include("apps.assessments.urls")),
    path("api/v1/directory/", include("apps.directory.urls")),
    path("api/v1/platform/", include("apps.platform_ops.urls")),
]

