class VoiceAssistant {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.currentAudio = null;
                
        this.init();
    }
    
    init() {
        // Check browser support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.error('Voice features not supported in this browser');
            return;
        }
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
    }
    
    setupUI() {
        // Add voice panel before chat input container
        const chatInputContainer = document.querySelector('.chat-input-container');
        if (chatInputContainer && !document.getElementById('voice-panel')) {
            const voicePanel = document.createElement('div');
            voicePanel.id = 'voice-panel';
            voicePanel.className = 'voice-panel';
            voicePanel.style.display = this.voiceEnabled ? 'block' : 'none';
            voicePanel.innerHTML = `
                <div class="voice-controls">
                    <button id="voice-record-btn" class="btn btn-primary" style="width: 100%;" title="Record voice query">
                        <i data-lucide="mic"></i>
                        <span>Record Voice Query</span>
                    </button>
                    <button id="voice-stop-btn" class="btn btn-primary" style="display: none; width: 100%; background: var(--error, #ef4444); border-color: var(--error, #ef4444);" title="Stop recording">
                        <i data-lucide="square"></i>
                        <span>Stop Recording</span>
                    </button>
                    <div id="voice-status" class="voice-status"></div>
                </div>
                <div id="voice-waveform" class="voice-waveform" style="display: none;">
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                </div>
            `;
            
            chatInputContainer.parentNode.insertBefore(voicePanel, chatInputContainer);
            
            // Initialize Lucide icons for the new elements
            if (window.lucide) {
                lucide.createIcons();
            }
        }
        
        // Add voice toggle button to chat input actions
        const inputActions = document.querySelector('.input-actions');
        if (inputActions) {
            const voiceToggleBtn = document.createElement('button');
            voiceToggleBtn.className = 'icon-btn';
            voiceToggleBtn.id = 'voice-toggle';
            voiceToggleBtn.title = this.voiceEnabled ? 'Voice mode is ON' : 'Voice mode is OFF';
            voiceToggleBtn.innerHTML = `<i data-lucide="${this.voiceEnabled ? 'mic' : 'mic-off'}" size="20"></i>`;
            voiceToggleBtn.addEventListener('click', () => this.toggleVoiceMode());

            // Prepend it so it appears first in the list of buttons
            inputActions.prepend(voiceToggleBtn);
 
            if (window.lucide) {
                lucide.createIcons();
            }
        }

        // Attach event listeners
        this.attachEventListeners();
    }
    
    addVoiceToggle() {
        const headerStats = document.querySelector('.header-stats');
        if (headerStats && !document.getElementById('voice-toggle')) {
            const voiceToggle = document.createElement('div');
            voiceToggle.id = 'voice-toggle';
            voiceToggle.className = 'voice-toggle' + (this.voiceEnabled ? ' active' : '');
            voiceToggle.innerHTML = `
                <i data-lucide="mic"></i>
                <span>${this.voiceEnabled ? 'Voice On' : 'Voice Off'}</span>
            `;
            voiceToggle.addEventListener('click', () => this.toggleVoiceMode());
            headerStats.appendChild(voiceToggle);
            
            // Initialize icon
            if (window.lucide) {
                lucide.createIcons();
            }
        }
    }
    
    toggleVoiceMode() {
        this.voiceEnabled = !this.voiceEnabled;
        localStorage.setItem('voice-enabled', this.voiceEnabled);
    
        const voicePanel = document.getElementById('voice-panel');
        const voiceToggle = document.getElementById('voice-toggle'); // This is now our icon button
    
        if (voicePanel) {
            voicePanel.style.display = this.voiceEnabled ? 'block' : 'none';
        }
    
        if (voiceToggle) {
            // Update the button's icon and title
            voiceToggle.title = this.voiceEnabled ? 'Voice mode is ON' : 'Voice mode is OFF';
            voiceToggle.innerHTML = `<i data-lucide="${this.voiceEnabled ? 'mic' : 'mic-off'}" size="20"></i>`;
      
            // Re-render the new icon
            if (window.lucide) {
                lucide.createIcons();
            }
        }
        
        this.showNotification(
            `Voice mode ${this.voiceEnabled ? 'enabled' : 'disabled'}`, 'success'
        );
    }
    
    attachEventListeners() {
        const recordBtn = document.getElementById('voice-record-btn');
        const stopBtn = document.getElementById('voice-stop-btn');
        
        if (recordBtn) {
            recordBtn.addEventListener('click', () => this.startRecording());
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopRecording());
        }
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            const recordBtn = document.getElementById('voice-record-btn');
            const stopBtn = document.getElementById('voice-stop-btn');
            const waveform = document.getElementById('voice-waveform');
            
            if (recordBtn) {
                recordBtn.style.display = 'none';
                recordBtn.classList.add('recording');
            }
            if (stopBtn) stopBtn.style.display = 'flex';
            if (waveform) waveform.style.display = 'flex';
            
            this.updateStatus('🎤 Recording... Click stop when done');
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.showNotification(
                'Could not access microphone. Please check permissions.',
                'error'
            );
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Stop all tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            // Update UI
            const recordBtn = document.getElementById('voice-record-btn');
            const stopBtn = document.getElementById('voice-stop-btn');
            const waveform = document.getElementById('voice-waveform');
            
            if (recordBtn) {
                recordBtn.style.display = 'flex';
                recordBtn.classList.remove('recording');
            }
            if (stopBtn) stopBtn.style.display = 'none';
            if (waveform) waveform.style.display = 'none';
            
            this.updateStatus('Processing your query...');
        }
    }
    
    async processRecording() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        await this.sendVoiceQuery(audioBlob);
    }
    
    async sendVoiceQuery(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            const response = await fetch('/api/voice/query', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Voice query failed');
            }
            
            const data = await response.json();
            
            // Display results in chat
            this.displayResults(data);
            
            // Play audio response if available
            if (data.audio_base64) {
                this.playAudioResponse(data.audio_base64);
            }
            
            this.updateStatus('');
            this.showNotification('✨ Voice query completed!', 'success');
            
        } catch (error) {
            console.error('Error processing voice query:', error);
            this.updateStatus('');
            this.showNotification(
                'Error processing voice query. Please try again.',
                'error'
            );
        }
    }
    
    displayResults(data) {
        // Get chat messages container
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        // Remove empty state if present
        const emptyState = chatMessages.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }
        
        // Add user message (transcribed text)
        const userMessage = this.createMessageElement('user', data.transcribed_text);
        chatMessages.appendChild(userMessage);
        
        // Add AI response
        const aiMessage = this.createMessageElement('ai', data.response_text, {
            route: data.route,
            latency: data.latency,
            audioBase64: data.audio_base64
        });
        chatMessages.appendChild(aiMessage);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Initialize Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }
    
    createMessageElement(role, content, metadata = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ' + role;
        const avatarClass = role === 'user' ? 'user-avatar' : 'ai-avatar';
        const icon = role === 'user' ? 'user' : 'bot';
        
        let metadataHtml = '';
        if (metadata) {
            metadataHtml = `
                <div class="voice-result">
                    <div class="metadata">
                        <span class="badge">
                            <i data-lucide="route"></i> ${metadata.route}
                        </span>
                        <span class="badge">
                            <i data-lucide="clock"></i> ${metadata.latency.toFixed(2)}s
                        </span>
                        <span class="badge">
                            <i data-lucide="mic"></i> Voice Query
                        </span>
                    </div>
                    ${metadata.audioBase64 ? `
                        <div class="audio-controls">
                            <button class="btn-play" onclick="window.voiceAssistant.playAudio('${metadata.audioBase64}')">
                                <i data-lucide="play"></i>
                                <span>Play Response</span>
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar ${avatarClass}">
                <i data-lucide="${icon}" size="20" color="white"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${this.formatText(content)}</div>
                ${metadataHtml}
            </div>
        `;
        
        return messageDiv;
    }
    
    formatText(text) {
        // Basic formatting (handles markdown-like syntax)
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
    
    playAudio(base64Audio) {
        this.playAudioResponse(base64Audio);
    }
    
    playAudioResponse(base64Audio) {
        // Stop any currently playing audio
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        
        try {
            // Create and play audio
            const audio = new Audio(`data:audio/mpeg;base64,${base64Audio}`);
            this.currentAudio = audio;
            
            audio.play().catch(error => {
                console.error('Error playing audio:', error);
                this.showNotification('Error playing audio', 'error');
            });
            
            // Show playing notification
            this.showNotification('🔊 Playing response...', 'info');
            
        } catch (error) {
            console.error('Error creating audio:', error);
            this.showNotification('Error playing audio', 'error');
        }
    }
    
    updateStatus(message) {
        const statusEl = document.getElementById('voice-status');
        if (statusEl) {
            statusEl.textContent = message;
            statusEl.className = message ? 'voice-status active' : 'voice-status';
        }
    }
    
    showNotification(message, type = 'info') {
        // Remove any existing notifications
        const existing = document.querySelectorAll('.notification');
        existing.forEach(n => n.remove());
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const iconMap = {
            success: 'check-circle',
            error: 'x-circle',
            info: 'info'
        };
        
        notification.innerHTML = `
            <i data-lucide="${iconMap[type] || 'info'}"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        // Initialize icon
        if (window.lucide) {
            lucide.createIcons();
        }
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Alternative: Simple text-to-speech function
async function speakText(text) {
    try {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('lang', 'en');
        
        const response = await fetch('/api/voice/synthesize', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('TTS failed');
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
        
    } catch (error) {
        console.error('Error speaking text:', error);
    }
}

// Initialize voice assistant
window.voiceAssistant = new VoiceAssistant();
window.speakText = speakText;