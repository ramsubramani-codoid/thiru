from django.urls import path
from . import views

urlpatterns = [
    path('whatsapp/', views.WhatsappView.as_view(), name = 'whatsapp_view'),
    path('chat/<id>', views.ChatView.as_view(), name = 'chat_view'),
    path('chat/', views.ChatView.as_view(), name = 'chat_send_view'),
    # path('facebook/', views.FacebookView.as_view(), name = 'facebook_view'),
]