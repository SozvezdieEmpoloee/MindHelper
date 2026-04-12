from django.utils import timezone
from rest_framework import response, viewsets, views

from apps.common.permissions import IsAdminUserAccount

from .models import ModerationCase, NeuralModelVersion, SiteContent
from .selectors import build_admin_dashboard_stats
from .serializers import ModerationCaseSerializer, NeuralModelVersionSerializer, SiteContentSerializer
from .services import activate_model_version


class AdminStatsAPIView(views.APIView):
    permission_classes = (IsAdminUserAccount,)

    def get(self, request):
        return response.Response(build_admin_dashboard_stats())


class NeuralModelVersionViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUserAccount,)
    serializer_class = NeuralModelVersionSerializer
    queryset = NeuralModelVersion.objects.all()

    def perform_create(self, serializer):
        instance = serializer.save(created_by_admin_user=self.request.user)
        if instance.is_active:
            activate_model_version(model_version=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.is_active:
            activate_model_version(model_version=instance)


class ModerationCaseViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUserAccount,)
    serializer_class = ModerationCaseSerializer
    queryset = ModerationCase.objects.select_related("chat", "message", "opened_by_admin_user")

    def perform_create(self, serializer):
        serializer.save(opened_by_admin_user=self.request.user)


class SiteContentViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUserAccount,)
    serializer_class = SiteContentSerializer
    queryset = SiteContent.objects.all()

    def perform_create(self, serializer):
        serializer.save(updated_by_admin_user=self.request.user, updated_at=timezone.now())

    def perform_update(self, serializer):
        serializer.save(updated_by_admin_user=self.request.user, updated_at=timezone.now())
