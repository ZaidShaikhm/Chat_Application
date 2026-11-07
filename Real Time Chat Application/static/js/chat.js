/**
 * DjangoChat - Real-Time Chat Engine
 * Handles WebSockets, UI updates, Typing Indicators, Audio Beeps, and File Attachments
 */

class ChatClient {
    constructor(config) {
        this.roomType = config.roomType; // 'private' or 'group'
        this.roomId = config.roomId;     // conversation_id or group_id
        this.currentUserId = config.currentUserId;
        this.currentUsername = config.currentUsername;
        this.messagesContainer = document.getElementById('chatMessagesContainer');
        this.messageInput = document.getElementById('chatMessageInput');
        this.sendBtn = document.getElementById('chatSendBtn');
        this.fileInput = document.getElementById('chatFileInput');
        this.filePreviewBar = document.getElementById('filePreviewBar');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.typingUserText = document.getElementById('typingUserText');

        this.socket = null;
        this.typingTimeout = null;
        this.isTyping = false;
        this.reconnectAttempts = 0;

        this.init();
    }

    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.scrollToBottom(false);
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const endpoint = this.roomType === 'private'
            ? `/ws/chat/${this.roomId}/`
            : `/ws/group/${this.roomId}/`;

        const socketUrl = `${protocol}${window.location.host}${endpoint}`;
        console.log(`[WebSocket] Connecting to ${socketUrl}...`);

        this.socket = new WebSocket(socketUrl);

        this.socket.onopen = (e) => {
            console.log('[WebSocket] Connected successfully.');
            this.reconnectAttempts = 0;
            this.updateConnectionBadge(true);
            if (this.roomType === 'private') {
                this.socket.send(JSON.stringify({ 'type': 'mark_read' }));
            }
        };

        this.socket.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                this.handleSocketEvent(data);
            } catch (err) {
                console.error('[WebSocket] Error parsing incoming message:', err);
            }
        };

        this.socket.onclose = (e) => {
            console.warn('[WebSocket] Connection closed. Code:', e.code);
            this.updateConnectionBadge(false);
            // Attempt reconnect with backoff
            if (this.reconnectAttempts < 8) {
                const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 10000);
                this.reconnectAttempts++;
                console.log(`[WebSocket] Reconnecting in ${delay}ms... (Attempt ${this.reconnectAttempts})`);
                setTimeout(() => this.connectWebSocket(), delay);
            }
        };

        this.socket.onerror = (err) => {
            console.error('[WebSocket] Error occurred:', err);
        };
    }

    updateConnectionBadge(connected) {
        const badge = document.getElementById('wsStatusBadge');
        if (badge) {
            if (connected) {
                badge.className = 'badge bg-success-subtle text-success border border-success-subtle';
                badge.innerText = 'Connected';
            } else {
                badge.className = 'badge bg-warning-subtle text-warning border border-warning-subtle';
                badge.innerText = 'Reconnecting...';
            }
        }
    }

    setupEventListeners() {
        // Send button click
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSendMessage();
            });
        }

        // Enter key in input field
        if (this.messageInput) {
            this.messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage();
                }
            });
            this.messageInput.addEventListener('input', () => {
                this.handleTyping();
            });
        }

        // File attachment input change
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.showFilePreview(file);
                }
            });
        }

        // Cancel file attachment preview
        const cancelFileBtn = document.getElementById('cancelFileBtn');
        if (cancelFileBtn) {
            cancelFileBtn.addEventListener('click', () => {
                this.clearFilePreview();
            });
        }
    }

    handleSendMessage() {
        // Check if there is a file selected
        if (this.fileInput && this.fileInput.files.length > 0) {
            this.uploadFile();
            return;
        }

        const message = this.messageInput.value.trim();
        if (!message) return;

        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                'type': 'chat_message',
                'message': message
            }));
            this.messageInput.value = '';
            this.sendStopTyping();
        } else {
            alert('Not connected to chat server. Please wait or reload.');
        }
    }

    handleTyping() {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;

        if (!this.isTyping) {
            this.isTyping = true;
            this.socket.send(JSON.stringify({
                'type': 'typing',
                'is_typing': true
            }));
        }

        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.sendStopTyping();
        }, 1500);
    }

    sendStopTyping() {
        if (this.isTyping && this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.isTyping = false;
            this.socket.send(JSON.stringify({
                'type': 'typing',
                'is_typing': false
            }));
        }
    }

    handleSocketEvent(data) {
        switch (data.type) {
            case 'chat_message_forward':
                this.appendMessage(data);
                this.scrollToBottom(true);
                if (data.sender_id !== this.currentUserId) {
                    this.playNotificationSound();
                    if (this.roomType === 'private' && this.socket && this.socket.readyState === WebSocket.OPEN) {
                        this.socket.send(JSON.stringify({ 'type': 'mark_read' }));
                    }
                }
                break;

            case 'typing_status':
                if (data.sender_id !== this.currentUserId) {
                    this.updateTypingIndicator(data.is_typing, data.sender_name || data.sender_username);
                }
                break;

            case 'user_status':
                this.updateUserPresence(data.user_id, data.status);
                break;

            case 'read_receipt':
                this.markAllMessagesAsRead();
                break;

            default:
                console.log('[WebSocket] Unhandled event:', data);
        }
    }

    appendMessage(data) {
        if (!this.messagesContainer) return;

        const isMe = data.sender_id === this.currentUserId;
        const messageRow = document.createElement('div');
        messageRow.className = `message-row ${isMe ? 'sent' : 'received'}`;
        messageRow.id = `msg-${data.message_id}`;

        // Sender Avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'avatar avatar-sm';
        if (data.sender_avatar) {
            avatarDiv.innerHTML = `<img src="${data.sender_avatar}" alt="${data.sender_username}" class="avatar avatar-sm">`;
        } else {
            const initial = (data.sender_name || data.sender_username || '?').charAt(0).toUpperCase();
            avatarDiv.innerText = initial;
        }

        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';

        // In group chat, show sender name for received messages
        if (this.roomType === 'group' && !isMe) {
            const senderName = document.createElement('div');
            senderName.className = 'message-sender-name';
            senderName.innerText = data.sender_name || data.sender_username;
            contentWrapper.appendChild(senderName);
        }

        // Message text bubble
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerText = data.message;

        // Render attachments if any
        if (data.attachments && data.attachments.length > 0) {
            data.attachments.forEach(att => {
                const attCard = document.createElement('div');
                attCard.className = 'attachment-card';
                if (att.is_image) {
                    attCard.innerHTML = `
                        <a href="${att.file_url}" target="_blank">
                            <img src="${att.file_url}" alt="${att.file_name}" class="attachment-img">
                        </a>
                    `;
                } else {
                    attCard.innerHTML = `
                        <a href="${att.file_url}" target="_blank" class="attachment-file" download>
                            <i class="bi bi-file-earmark-arrow-down fs-5"></i>
                            <div>
                                <div class="fw-semibold text-truncate" style="max-width: 180px;">${att.file_name}</div>
                                <small class="opacity-75">${att.file_size || 'Download'}</small>
                            </div>
                        </a>
                    `;
                }
                bubble.appendChild(attCard);
            });
        }

        contentWrapper.appendChild(bubble);

        // Metadata (Time & checkmark)
        const meta = document.createElement('div');
        meta.className = 'message-meta';
        meta.innerHTML = `
            <span>${data.time_display || 'Just now'}</span>
            ${isMe ? '<i class="bi bi-check2 text-primary"></i>' : ''}
        `;
        contentWrapper.appendChild(meta);

        // Assemble row
        if (isMe) {
            messageRow.appendChild(contentWrapper);
            messageRow.appendChild(avatarDiv);
        } else {
            messageRow.appendChild(avatarDiv);
            messageRow.appendChild(contentWrapper);
        }

        this.messagesContainer.appendChild(messageRow);
    }

    updateTypingIndicator(isTyping, username) {
        if (!this.typingIndicator) return;
        if (isTyping) {
            if (this.typingUserText) {
                this.typingUserText.innerText = `${username} is typing...`;
            }
            this.typingIndicator.style.display = 'flex';
            this.scrollToBottom(true);
        } else {
            this.typingIndicator.style.display = 'none';
        }
    }

    updateUserPresence(userId, status) {
        const presenceIndicator = document.getElementById(`userStatus-${userId}`);
        const headerStatus = document.getElementById('chatHeaderPresence');
        
        if (status === 'online') {
            if (presenceIndicator) {
                presenceIndicator.classList.remove('status-offline');
                presenceIndicator.classList.add('status-online', 'pulse-online');
            }
            if (headerStatus) {
                headerStatus.innerHTML = '<span class="text-success"><i class="bi bi-circle-fill me-1" style="font-size: 8px;"></i>Online</span>';
            }
        } else {
            if (presenceIndicator) {
                presenceIndicator.classList.remove('status-online', 'pulse-online');
                presenceIndicator.classList.add('status-offline');
            }
            if (headerStatus) {
                headerStatus.innerHTML = '<span class="text-muted"><i class="bi bi-circle me-1" style="font-size: 8px;"></i>Offline</span>';
            }
        }
    }

    markAllMessagesAsRead() {
        const checkmarks = this.messagesContainer.querySelectorAll('.bi-check2');
        checkmarks.forEach(chk => {
            chk.className = 'bi bi-check2-all text-primary';
        });
    }

    showFilePreview(file) {
        if (!this.filePreviewBar) return;
        const nameEl = document.getElementById('previewFileName');
        const sizeEl = document.getElementById('previewFileSize');
        if (nameEl) nameEl.innerText = file.name;
        if (sizeEl) sizeEl.innerText = (file.size / 1024).toFixed(1) + ' KB';
        this.filePreviewBar.style.display = 'flex';
    }

    clearFilePreview() {
        if (this.fileInput) this.fileInput.value = '';
        if (this.filePreviewBar) this.filePreviewBar.style.display = 'none';
    }

    uploadFile() {
        const file = this.fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        if (this.roomType === 'private') {
            formData.append('conversation_id', this.roomId);
        } else {
            formData.append('group_id', this.roomId);
        }
        
        const messageText = this.messageInput ? this.messageInput.value.trim() : '';
        if (messageText) {
            formData.append('content', messageText);
        }

        // Get CSRF Token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

        // Show uploading state
        if (this.sendBtn) {
            this.sendBtn.disabled = true;
            this.sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
        }

        fetch('/api/upload/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => response.json())
        .then(res => {
            this.clearFilePreview();
            if (this.messageInput) this.messageInput.value = '';
        })
        .catch(err => {
            console.error('File upload error:', err);
            alert('Failed to upload file. Please try again.');
        })
        .finally(() => {
            if (this.sendBtn) {
                this.sendBtn.disabled = false;
                this.sendBtn.innerHTML = '<i class="bi bi-send-fill"></i>';
            }
        });
    }

    scrollToBottom(smooth = true) {
        if (!this.messagesContainer) return;
        this.messagesContainer.scrollTo({
            top: this.messagesContainer.scrollHeight,
            behavior: smooth ? 'smooth' : 'auto'
        });
    }

    playNotificationSound() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
            osc.frequency.setValueAtTime(880, ctx.currentTime + 0.08); // A5
            gain.gain.setValueAtTime(0.1, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.25);
        } catch (e) {
            // Audio context policy might require user gesture first
        }
    }
}

// Global Dark Mode Controller
function initThemeToggle() {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const storedTheme = localStorage.getItem('django_chat_theme') || 'light';
    
    document.documentElement.setAttribute('data-bs-theme', storedTheme);
    updateThemeIcon(storedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('django_chat_theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeToggleIcon');
    if (icon) {
        if (theme === 'dark') {
            icon.className = 'bi bi-sun-fill text-warning';
        } else {
            icon.className = 'bi bi-moon-stars-fill text-secondary';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
});
