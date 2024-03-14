from django.urls import path
from . import views

urlpatterns = [
    path('scribe-simple-operation/', views.FineTuneModelOperation.as_view(), name='FineTuneModelOperation'),
    path('chat-bot/completions/', views.ChatBotCompletion.as_view(), name='ChatBotCompletion'),
    path('scribe/stripe/customer/get', views.StripeCustomerData.as_view(), name='StripeCustomerData'),
    path('scribe/stripe/payment-methods/list', views.StripeListPaymentMethods.as_view(), name='StripeListPaymentMethods'),
]
