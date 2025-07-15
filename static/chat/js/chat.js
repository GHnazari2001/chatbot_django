document.addEventListener('DOMContentLoaded', function() {
    // --- توابع کمکی ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function addMessage(content, type) {
        const messageList = document.getElementById('message-list');
        if (!messageList) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        bubbleDiv.innerHTML = content.replace(/\n/g, '<br>');
        messageDiv.appendChild(bubbleDiv);
        messageList.appendChild(messageDiv);
        messageList.scrollTop = messageList.scrollHeight;
    }

    // --- منطق اصلی صفحه ---
    const chatForm = document.getElementById('chat-form');
    if (!chatForm) return;

    const messageInput = document.getElementById('message-input');
    const messageList = document.getElementById('message-list');
    const chatContainer = document.querySelector('.chat-container');
    const chatId = chatContainer.dataset.chatId;

    if (messageList) {
        messageList.scrollTop = messageList.scrollHeight;
    }

    // --- رویداد ارسال فرم ---
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const userMessage = messageInput.value.trim();
        let postURL;

        if (chatId === 'guest') {
            postURL = '/chat/guest/send/';
        } else {
            postURL = `/chat/${chatId}/send/`;
        }

        if (userMessage) {
            addMessage(userMessage, 'user');
            messageInput.value = '';
            fetch(postURL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ message: userMessage })
            })
            .then(response => response.json())
            .then(data => {
                if (data.bot_response) addMessage(data.bot_response, 'bot');
                else if (data.error) addMessage(`خطا: ${data.error}`, 'bot');
            })
            .catch(error => {
                console.error('Error:', error);
                addMessage('متاسفانه خطایی در ارتباط با سرور رخ داد.', 'bot');
            });
        }
    });

    // =======================================================
    // ====== منطق میکروفن (گفتار به متن) ======
    // =======================================================
    const micButton = document.getElementById('mic-button');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'fa-IR';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        micButton.addEventListener('click', () => {
            if (micButton.disabled) return; // اگر دکمه غیرفعال بود، کاری نکن
            recognition.start();
        });

        recognition.onstart = () => {
            micButton.classList.add('is-recording');
        };

        recognition.onend = () => {
            micButton.classList.remove('is-recording');
        };

        recognition.onresult = (event) => {
            const speechResult = event.results[0][0].transcript;
            messageInput.value = speechResult;
        };

        recognition.onerror = (event) => {
            micButton.classList.remove('is-recording');
            alert('خطا در تشخیص گفتار: ' + event.error);
        };

    } else {
        // *** تغییر اینجاست ***
        // اگر مرورگر پشتیبانی نکرد، دکمه را غیرفعال و کم‌رنگ کن
        micButton.disabled = true;
        micButton.classList.add('mic-disabled');
        micButton.title = 'این قابلیت در مرورگر شما پشتیبانی نمی‌شود'; // افزودن راهنمای متنی
        console.log('مرورگر شما از قابلیت گفتار به متن پشتیبانی نمی‌کند.');
    }

    // --- بقیه رویدادها (سایدبار، منوی سه نقطه و...) ---
    // ... (این بخش بدون تغییر باقی می‌ماند) ...
    const toggleButton = document.getElementById('sidebar-toggle-btn');
    if (toggleButton) {
        const mainContainer = document.querySelector('.main-container');
        toggleButton.addEventListener('click', () => mainContainer.classList.toggle('sidebar-closed'));
    }
    document.querySelectorAll('.options-button').forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            const menu = this.nextElementSibling;
            document.querySelectorAll('.options-menu').forEach(m => {
                if (m !== menu) m.classList.remove('show');
            });
            menu.classList.toggle('show');
        });
    });
    window.addEventListener('click', () => {
        document.querySelectorAll('.options-menu').forEach(menu => menu.classList.remove('show'));
    });
    document.querySelectorAll('.delete-link').forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            if (confirm('آیا از حذف این گفتگو مطمئن هستید؟')) window.location.href = this.href;
        });
    });
    document.querySelectorAll('.rename-button').forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            const renameChatId = this.dataset.chatId;
            const currentTitle = this.closest('.chat-item').querySelector('.chat-link').textContent.trim();
            const newTitle = prompt('نام جدید گفتگو را وارد کنید:', currentTitle);
            if (newTitle && newTitle.trim() && newTitle !== currentTitle) {
                fetch(`/chat/${renameChatId}/rename/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ title: newTitle.trim() })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.closest('.chat-item').querySelector('.chat-link').textContent = data.new_title;
                        const mainChatTitle = document.querySelector('.chat-header h1');
                        if (mainChatTitle && chatContainer.dataset.chatId == renameChatId) {
                            mainChatTitle.textContent = data.new_title;
                        }
                    } else {
                        alert('خطا در تغییر نام: ' + (data.error || ''));
                    }
                });
            }
        });
    });
    document.querySelectorAll('.share-button').forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation();
            const chatUrl = new URL(this.dataset.chatUrl, window.location.origin).href;
            navigator.clipboard.writeText(chatUrl)
                .then(() => {
                    alert('لینک گفتگو کپی شد!');
                    this.closest('.options-menu').classList.remove('show');
                })
                .catch(() => alert('خطا در کپی کردن لینک.'));
        });
    });
});