from rest_framework import generics, permissions, response, views

from .models import CrisisEvent
from .selectors import get_user_chat_statistics
from .serializers import (
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    CrisisEventSerializer,
    UserChatSerializer,
)
from .services import create_chat_turn, get_or_create_user_chat


class CurrentUserChatAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        chat = get_or_create_user_chat(user=request.user)
        serializer = UserChatSerializer(chat)
        return response.Response(serializer.data)


class ChatMessageListCreateAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        chat = get_or_create_user_chat(user=request.user)
        serializer = ChatMessageSerializer(chat.messages.order_by("created_at"), many=True)
        return response.Response(serializer.data)

    def post(self, request):
        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat = get_or_create_user_chat(user=request.user)
        user_message, bot_message, crisis_event = create_chat_turn(
            chat=chat,
            content_text=serializer.validated_data["content_text"],
        )
        payload = {
            "user_message": ChatMessageSerializer(user_message).data,
            "bot_message": ChatMessageSerializer(bot_message).data,
            "crisis_event": CrisisEventSerializer(crisis_event).data if crisis_event else None,
            "chat_id": str(chat.id),
        }
        return response.Response(payload, status=201)


class UserChatStatsAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return response.Response(get_user_chat_statistics(request.user))


class CrisisEventListAPIView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CrisisEventSerializer

    def get_queryset(self):
        chat = get_or_create_user_chat(user=self.request.user)
        return CrisisEvent.objects.filter(chat=chat)
