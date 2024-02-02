from django.urls import path
from . import views

urlpatterns = [
    path('scribe-simple-operation/', views.FineTuneModelOperation.as_view(), name='FineTuneModelOperation'),
    path('chat-bot/completions/', views.ChatBotCompletion.as_view(), name='ChatBotCompletion'),
]
