# chat/models.py
from django.db import models
from django.contrib.auth.models import User

class Chat(models.Model):
    """
    مدلی برای نگهداری هر گفتگوی مستقل.
    هر گفتگو به یک کاربر تعلق دارد و یک عنوان دارد که می‌توان آن را
    بر اساس اولین پیام کاربر تنظیم کرد.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    title = models.CharField(max_length=100, default='گفتگوی جدید')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"'{self.title}' by {self.user.username}"

class Message(models.Model):
    """
    مدلی برای نگهداری هر پیام در یک گفتگو.
    هر پیام به یک گفتگوی خاص (Chat) مرتبط است و نوع آن
    (user یا bot) مشخص می‌شود.
    """

    # تعریف گزینه‌ها برای نوع پیام
    USER = 'user'
    BOT = 'bot'
    MESSAGE_TYPE_CHOICES = [
        (USER, 'User'),
        (BOT, 'Bot'),
    ]

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=4, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_message_type_display()} message in chat {self.chat.id}"