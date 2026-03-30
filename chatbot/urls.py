from django.urls import path
from .views import chatbot_api, chat_ui

urlpatterns = [
    path("api/", chatbot_api, name="chatbot_api"),
    path("ui/", chat_ui, name="chat_ui"),
]