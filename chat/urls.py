
from django.urls import path
from . import views

urlpatterns = [
    # URL برای کاربران لاگین کرده - این ویو یک چت جدید ساخته و به آن ریدایرکت می‌کند

    
    path('', views.public_chat_view, name='public_chat'),

    # این مسیر برای کاربران لاگین‌کرده است تا چت جدید بسازند
    path('new/', views.start_new_chat, name='start_new_chat'),

    # مسیر جدید برای پردازش پیام‌های حالت مهمان
    path('chat/guest/send/', views.send_guest_message, name='send_guest_message'),
    
    
    
    
    # URL برای نمایش یک چت موجود با شناسه مشخص
    path('chat/<int:chat_id>/', views.chat_view, name='chat_page'),
    path('chat/<int:chat_id>/rename/', views.rename_chat, name='rename_chat'),
  
    path('chat/<int:chat_id>/send/', views.send_message, name='send_message'),
    path('chat/<int:chat_id>/delete/', views.delete_chat, name='delete_chat'),
    
    # URLهای مربوط به احراز هویت
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]