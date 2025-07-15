# chat/views.py
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required

from .models import Chat, Message
from . import rag_service

# --- نماهای مربوط به ثبت‌نام و ورود ---

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('start_new_chat')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # اگر کاربر از صفحه دیگری آمده بود، به آن آدرس برگرد
                if 'next' in request.GET:
                    return redirect(request.GET.get('next'))
                return redirect('start_new_chat')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    # بعد از خروج، به صفحه چت عمومی برو
    return redirect('public_chat')

# --- ویوهای جدید برای حالت مهمان ---

def public_chat_view(request):
    """
    صفحه چت عمومی را برای همه کاربران نمایش می‌دهد.
    """
    context = {
        'is_guest_chat': True,
        'chat': {'title': 'گفتگوی عمومی', 'id': 'guest'}
    }
    if request.user.is_authenticated:
        context['user_chats'] = Chat.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'chat.html', context)

@require_POST
def send_guest_message(request):
    """
    پیام کاربر مهمان را دریافت و پاسخ را بدون ذخیره‌سازی برمی‌گرداند.
    """
    try:
        data = json.loads(request.body)
        user_message_content = data.get('message', '').strip()
        if not user_message_content:
            return JsonResponse({'error': 'پیام نمی‌تواند خالی باشد.'}, status=400)
        chat_history_for_rag = [{'message_type': 'user', 'content': user_message_content}]
        bot_response_content = rag_service.get_rag_response(
            user_query=user_message_content,
            chat_history=chat_history_for_rag
        )
        return JsonResponse({'bot_response': bot_response_content})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# --- نماهای اصلی برنامه چت برای کاربران لاگین کرده ---

@login_required
def start_new_chat(request):
    chat = Chat.objects.create(user=request.user)
    return redirect('chat_page', chat_id=chat.id)

@login_required
def chat_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    messages = chat.messages.all().order_by('created_at')
    user_chats = Chat.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'chat': chat,
        'messages': messages,
        'user_chats': user_chats,
    }
    return render(request, 'chat.html', context)

@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    chat.delete()
    return redirect('public_chat')

@login_required
@require_POST
def send_message(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    data = json.loads(request.body)
    user_message_content = data.get('message', '')
    if not user_message_content:
        return JsonResponse({'error': 'پیام نمی‌تواند خالی باشد.'}, status=400)
    Message.objects.create(chat=chat, message_type='user', content=user_message_content)
    if chat.messages.filter(message_type='user').count() == 1:
        truncated_title = user_message_content[:40]
        chat.title = f"{truncated_title}..." if len(user_message_content) > 40 else user_message_content
        chat.save()
    chat_history_for_rag = list(chat.messages.values('message_type', 'content'))
    bot_response_content = rag_service.get_rag_response(
        user_query=user_message_content,
        chat_history=chat_history_for_rag
    )
    bot_message = Message.objects.create(chat=chat, message_type='bot', content=bot_response_content)
    return JsonResponse({'bot_response': bot_message.content})

@login_required
@require_POST
def rename_chat(request, chat_id):
    try:
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        data = json.loads(request.body)
        new_title = data.get('title', '').strip()
        if not new_title:
            return JsonResponse({'success': False, 'error': 'عنوان نمی‌تواند خالی باشد.'}, status=400)
        chat.title = new_title
        chat.save()
        return JsonResponse({'success': True, 'new_title': chat.title})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)