class ChatWidget {
    constructor() {
        this.isOpen = false;
        this.isTyping = false;
        this.init();
    }

    init() {
        this.createWidget();
        this.attachEventListeners();
        this.addWelcomeMessage();
    }

    createWidget() {
        const widget = document.createElement('div');
        widget.className = 'chat-widget';
        widget.innerHTML = `
            <div class="chat-window" id="chatWindow">
                <div class="chat-header">
                    <span>🤖 AI Консультант</span>
                    <button class="close-btn" id="closeChatBtn">×</button>
                </div>
                <div class="chat-messages" id="chatMessages">
                    <!-- Сообщения будут добавляться здесь -->
                </div>
                <div class="chat-input-area">
                    <input type="text" class="chat-input" id="chatInput" placeholder="Спросите о товарах..." maxlength="200">
                    <button class="chat-send" id="chatSend">➤</button>
                </div>
            </div>
            <button class="chat-toggle" id="chatToggle">💬</button>
        `;
        document.body.appendChild(widget);
    }

    attachEventListeners() {
        const toggle = document.getElementById('chatToggle');
        const closeBtn = document.getElementById('closeChatBtn');
        const sendBtn = document.getElementById('chatSend');
        const input = document.getElementById('chatInput');

        toggle.addEventListener('click', () => this.toggleChat());
        closeBtn.addEventListener('click', () => this.closeChat());
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    toggleChat() {
        const window = document.getElementById('chatWindow');
        const toggle = document.getElementById('chatToggle');
        
        if (this.isOpen) {
            this.closeChat();
        } else {
            window.style.display = 'flex';
            toggle.innerHTML = '×';
            this.isOpen = true;
            setTimeout(() => document.getElementById('chatInput').focus(), 300);
        }
    }

    closeChat() {
        const window = document.getElementById('chatWindow');
        const toggle = document.getElementById('chatToggle');
        
        window.style.display = 'none';
        toggle.innerHTML = '💬';
        this.isOpen = false;
    }

    addWelcomeMessage() {
        setTimeout(() => {
            this.addBotMessage('Привіт! Я AI-консультант SmartShop 📱\nДопоможу підібрати смартфон. Яким бюджетом володієте?');
        }, 1000);
    }

    addUserMessage(text) {
        const messages = document.getElementById('chatMessages');
        const message = document.createElement('div');
        message.className = 'message user';
        message.innerHTML = `<div class="message-content">${this.escapeHtml(text)}</div>`;
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
    }

    addBotMessage(text) {
        const messages = document.getElementById('chatMessages');
        const message = document.createElement('div');
        message.className = 'message bot';
        
        // Преобразуем ссылки в кликабельные
        const formattedText = this.formatMessage(text);
        message.innerHTML = `<div class="message-content">${formattedText}</div>`;
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
    }

    formatMessage(text) {
        // Экранируем HTML
        let formatted = this.escapeHtml(text);
        
        // Преобразуем ссылки на товары
        formatted = formatted.replace(
            /(https?:\/\/[^\s]+\/product\/\d+)/g,
            '<a href="$1" target="_blank" style="color: #007bff; text-decoration: underline;">Посмотреть товар</a>'
        );
        
        // Преобразуем переносы строк
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }

    showTyping() {
        if (this.isTyping) return;
        
        const messages = document.getElementById('chatMessages');
        const typing = document.createElement('div');
        typing.className = 'message bot';
        typing.id = 'typingIndicator';
        typing.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        messages.appendChild(typing);
        messages.scrollTop = messages.scrollHeight;
        this.isTyping = true;
    }

    hideTyping() {
        const typing = document.getElementById('typingIndicator');
        if (typing) {
            typing.remove();
            this.isTyping = false;
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatInput');
        const sendBtn = document.getElementById('chatSend');
        const message = input.value.trim();
        
        if (!message || this.isTyping) return;
        
        // Добавляем сообщение пользователя
        this.addUserMessage(message);
        input.value = '';
        sendBtn.disabled = true;
        
        // Показываем индикатор печати
        this.showTyping();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            this.hideTyping();
            
            if (response.ok && data.message) {
                this.addBotMessage(data.message);
            } else if (data.error) {
                this.addBotMessage(`⚠️ ${data.error}`);
            } else {
                this.addBotMessage('Извините, произошла ошибка. Попробуйте еще раз.');
            }
        } catch (error) {
            console.error('Ошибка чата:', error);
            this.hideTyping();
            this.addBotMessage('Ошибка соединения. Проверьте интернет и попробуйте снова.');
        }
        
        sendBtn.disabled = false;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Инициализация чат-виджета после загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    new ChatWidget();
});