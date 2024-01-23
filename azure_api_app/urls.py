from django.urls import path
from . import views

urlpatterns = [
    path('completions/', views.FineTuneModelCompletion.as_view(), name='FineTuneModelCompletion'),
    path('audio-to-text/', views.AssemblyAIAudioToText.as_view(), name='AssemblyAIAudioToText'),
    path('audio-to-text-status/<str:transcript_id>', views.AssemblyAIAudioToTextStatus.as_view(), name='AssemblyAIAudioToTextStatus'),
    path('chat-bot/completions/', views.ChatBotCompletion.as_view(), name='ChatBotCompletion'),
]
