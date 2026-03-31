from django.urls import path
from .views import chatbot_ask

urlpatterns = [
    path("chatbot/ask/", chatbot_ask, name="chatbot_ask"),
]