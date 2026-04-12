from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminStatsAPIView, ModerationCaseViewSet, NeuralModelVersionViewSet, SiteContentViewSet


router = DefaultRouter()
router.register("model-versions", NeuralModelVersionViewSet, basename="model-version")
router.register("moderation-cases", ModerationCaseViewSet, basename="moderation-case")
router.register("site-content", SiteContentViewSet, basename="site-content")

urlpatterns = [
    path("stats/", AdminStatsAPIView.as_view(), name="platform-admin-stats"),
    path("", include(router.urls)),
]
