from django.urls import path

from .views import (
    ChatMessageListCreateAPIView,
    CrisisEventListAPIView,
    CurrentUserChatAPIView,
    UserChatStatsAPIView,
)


urlpatterns = [
    path("me/", CurrentUserChatAPIView.as_view(), name="chat-me"),
    path("messages/", ChatMessageListCreateAPIView.as_view(), name="chat-messages"),
    path("crisis-events/", CrisisEventListAPIView.as_view(), name="chat-crisis-events"),
    path("stats/", UserChatStatsAPIView.as_view(), name="chat-stats"),
]
