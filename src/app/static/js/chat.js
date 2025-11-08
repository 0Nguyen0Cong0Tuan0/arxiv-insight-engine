const Chat = {
    init() {
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const imageUploadBtn = document.getElementById('imageUploadBtn');
        const imageInput = document.getElementById('imageInput');
        
        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Enter to send
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button click
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Image upload
        imageUploadBtn.addEventListener('click', () => imageInput.click());
        
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    AppState.setUploadedImage(e.target.result);
                    UI.showToast('Image uploaded! Add a message and send.', 'success');
                };
                reader.readAsDataURL(file);
            }
        });
    },
    
    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message && !AppState.uploadedImage) return;
        
        // Clear empty state
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages.querySelector('.empty-state')) {
            chatMessages.innerHTML = '';
        }
        
        // Add user message
        this.addMessage('user', message, AppState.uploadedImage);
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        const imageToSend = AppState.uploadedImage;
        AppState.clearUploadedImage();
        
        // Show typing indicator
        const typingId = this.addTypingIndicator();
        
        try {
            const data = await API.queryText(
                message,
                imageToSend ? imageToSend.split(',')[1] : null
            );
            
            this.removeTypingIndicator(typingId);
            
            let aiMessage = data.response;
            if (data.image_caption) {
                aiMessage = `[Image Analysis: ${data.image_caption}]\n\n${aiMessage}`;
            }
            
            this.addMessage('ai', aiMessage);
        } catch (error) {
            console.error('Query error:', error);
            this.removeTypingIndicator(typingId);
            this.addMessage('ai', 'Sorry, I encountered an error processing your request. Please try again.');
        }
    },
    
    addMessage(type, text, image = null) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const avatarIcon = type === 'user' ? 'user' : 'bot';
        
        messageDiv.innerHTML = `
            <div class="message-avatar ${type}-avatar">
                <i data-lucide="${avatarIcon}" size="20" color="white"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${text.replace(/\n/g, '<br>')}</div>
                ${image ? `<img src="${image}" class="message-image" alt="Uploaded image">` : ''}
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        lucide.createIcons();
        chatMessages.scrollTop = chatMessages.scrollHeight;
    },
    
    addTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const id = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai';
        typingDiv.id = id;
        
        typingDiv.innerHTML = `
            <div class="message-avatar ai-avatar">
                <i data-lucide="bot" size="20" color="white"></i>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        lucide.createIcons();
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    },
    
    removeTypingIndicator(id) {
        const element = document.getElementById(id);
        if (element) element.remove();
    }
};