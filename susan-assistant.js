/**
 * Enhanced Susan Virtual Assistant - Conversational Chat Widget
 * Sports Schedulers Web Application
 * Author: Jose Ortiz
 * Copyright: 2025
 * 
 * Enhanced with natural conversation capabilities, personality, and memory
 */

class EnhancedSusanAssistant {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.isTyping = false;
        this.currentPage = this.detectCurrentPage();
        this.conversationMemory = new Map();
        this.userPreferences = {};
        
        // Enhanced personality settings
        this.personality = {
            friendly: true,
            enthusiastic: true,
            supportive: true,
            professional: true
        };
        
        // Conversation state
        this.conversationContext = {
            lastTopic: null,
            emotionalState: 'neutral',
            helpLevel: 'beginner'
        };
        
        this.init();
    }

    detectCurrentPage() {
        const path = window.location.pathname;
        if (path === '/official' || path.includes('/official')) {
            return 'official';
        }
        if (path === '/' || path === '/dashboard') {
            return 'dashboard';
        }
        return 'general';
    }

    init() {
        this.createEnhancedChatWidget();
        this.bindEvents();
        this.loadPersonalizedWelcome();
        this.initializeConversationMemory();
    }

    createEnhancedChatWidget() {
        // Create main container with enhanced styling
        this.container = document.createElement('div');
        this.container.id = 'susan-assistant';
        this.container.className = 'susan-assistant enhanced';
        this.container.innerHTML = `
            <!-- Enhanced Chat Toggle Button -->
            <div id="susan-toggle" class="susan-toggle enhanced">
                <div class="susan-avatar">
                    <span class="susan-initial">S</span>
                    <div class="susan-status online"></div>
                    <div class="susan-pulse"></div>
                </div>
                <div class="susan-tooltip">
                    Hi! I'm Susan 😊<br>
                    <span class="tooltip-subtitle">Click to chat!</span>
                </div>
            </div>

            <!-- Enhanced Chat Window -->
            <div id="susan-chat" class="susan-chat enhanced">
                <div class="susan-header">
                    <div class="susan-header-info">
                        <div class="susan-avatar-header">
                            <span>S</span>
                            <div class="susan-mood-indicator" id="susan-mood">😊</div>
                        </div>
                        <div class="susan-info">
                            <div class="susan-name">Susan</div>
                            <div class="susan-subtitle">Your Friendly Assistant</div>
                            <div class="susan-status-text" id="susan-status">Online and ready to chat!</div>
                        </div>
                    </div>
                    <div class="susan-controls">
                        <button id="susan-mood-btn" class="susan-control-btn" title="Susan's mood">
                            😊
                        </button>
                        <button id="susan-minimize" class="susan-control-btn" title="Minimize">
                            <i class="fas fa-minus"></i>
                        </button>
                        <button id="susan-close" class="susan-control-btn" title="Close">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>

                <div class="susan-messages enhanced" id="susan-messages">
                    <!-- Messages will be dynamically added here -->
                </div>

                <div class="susan-typing enhanced" id="susan-typing" style="display: none;">
                    <div class="susan-typing-avatar">
                        <span>S</span>
                    </div>
                    <div class="susan-typing-content">
                        <div class="susan-typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        <span class="susan-typing-text">Susan is thinking...</span>
                    </div>
                </div>

                <div class="susan-suggestions" id="susan-suggestions">
                    <!-- Dynamic suggestions will appear here -->
                </div>

                <div class="susan-input-area enhanced">
                    <div class="susan-quick-actions" id="susan-quick-actions">
                        ${this.getEnhancedQuickActionsHTML()}
                    </div>
                    <div class="susan-input-container">
                        <input 
                            type="text" 
                            id="susan-input" 
                            class="susan-input enhanced" 
                            placeholder="Chat with Susan... 💬"
                            autocomplete="off"
                            maxlength="500"
                        >
                        <button id="susan-send" class="susan-send-btn enhanced">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                    <div class="susan-input-footer">
                        <span class="character-count" id="character-count">0/500</span>
                        <span class="susan-help-hint">💡 Try: "Hi Susan!" or "Help with games"</span>
                    </div>
                </div>
            </div>
        `;

        // Add enhanced CSS styles
        this.addEnhancedStyles();

        // Append to body
        document.body.appendChild(this.container);
    }

    getEnhancedQuickActionsHTML() {
        const commonActions = `
            <button class="susan-quick-btn conversation" data-message="Hi Susan! How are you?">
                <i class="fas fa-hand-wave"></i> Say Hi
            </button>
            <button class="susan-quick-btn conversation" data-message="Tell me a joke!">
                <i class="fas fa-laugh"></i> Joke
            </button>
        `;

        if (this.currentPage === 'official') {
            return `
                ${commonActions}
                <button class="susan-quick-btn official" data-message="How do I view my games?">
                    <i class="fas fa-calendar"></i> My Games
                </button>
                <button class="susan-quick-btn official" data-message="How do I set availability?">
                    <i class="fas fa-clock"></i> Availability
                </button>
            `;
        } else {
            return `
                ${commonActions}
                <button class="susan-quick-btn admin" data-message="How do I add games?">
                    <i class="fas fa-plus"></i> Add Games
                </button>
                <button class="susan-quick-btn admin" data-message="Help with officials">
                    <i class="fas fa-users"></i> Officials
                </button>
            `;
        }
    }

    addEnhancedStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Enhanced Susan Assistant Styles */
            .susan-assistant.enhanced {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 10000;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            .susan-toggle.enhanced {
                position: relative;
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
                transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                border: 3px solid rgba(255, 255, 255, 0.2);
                overflow: hidden;
            }

            .susan-toggle.enhanced:hover {
                transform: translateY(-5px) scale(1.05);
                box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
            }

            .susan-toggle.enhanced:active {
                transform: translateY(-2px) scale(1.02);
            }

            .susan-avatar {
                position: relative;
                width: 45px;
                height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .susan-initial {
                color: white;
                font-size: 24px;
                font-weight: bold;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }

            .susan-status.online {
                position: absolute;
                bottom: 2px;
                right: 2px;
                width: 16px;
                height: 16px;
                background: #10b981;
                border: 3px solid white;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }

            .susan-pulse {
                position: absolute;
                top: 50%;
                left: 50%;
                width: 100%;
                height: 100%;
                border: 2px solid rgba(255, 255, 255, 0.6);
                border-radius: 50%;
                transform: translate(-50%, -50%);
                animation: ripple 2s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(1.1); }
            }

            @keyframes ripple {
                0% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
                100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
            }

            .susan-tooltip {
                position: absolute;
                bottom: 80px;
                right: 0;
                background: rgba(51, 51, 51, 0.95);
                color: white;
                padding: 12px 16px;
                border-radius: 12px;
                font-size: 14px;
                white-space: nowrap;
                opacity: 0;
                visibility: hidden;
                transform: translateY(10px);
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                text-align: center;
                line-height: 1.4;
            }

            .susan-toggle.enhanced:hover .susan-tooltip {
                opacity: 1;
                visibility: visible;
                transform: translateY(0);
            }

            .tooltip-subtitle {
                font-size: 12px;
                opacity: 0.8;
                display: block;
                margin-top: 2px;
            }

            .susan-chat.enhanced {
                position: absolute;
                bottom: 80px;
                right: 0;
                width: 480px;
                height: 650px;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
                display: flex;
                flex-direction: column;
                transform: scale(0.8) translateY(20px);
                opacity: 0;
                visibility: hidden;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                border: 1px solid rgba(0, 0, 0, 0.05);
                overflow: hidden;
            }

            .susan-chat.enhanced.open {
                transform: scale(1) translateY(0);
                opacity: 1;
                visibility: visible;
            }

            .susan-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-radius: 20px 20px 0 0;
                position: relative;
            }

            .susan-header::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            }

            .susan-header-info {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .susan-avatar-header {
                position: relative;
                width: 45px;
                height: 45px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }

            .susan-mood-indicator {
                position: absolute;
                bottom: -2px;
                right: -2px;
                font-size: 16px;
                background: white;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .susan-info {
                flex: 1;
            }

            .susan-name {
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 2px;
            }

            .susan-subtitle {
                font-size: 13px;
                opacity: 0.9;
                margin-bottom: 2px;
            }

            .susan-status-text {
                font-size: 11px;
                opacity: 0.8;
                font-style: italic;
            }

            .susan-controls {
                display: flex;
                gap: 8px;
            }

            .susan-control-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                transition: all 0.2s ease;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .susan-control-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: scale(1.1);
            }

            .susan-messages.enhanced {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 16px;
                background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
            }

            .susan-message {
                max-width: 85%;
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 14px;
                line-height: 1.5;
                position: relative;
                animation: messageSlideIn 0.3s ease-out;
            }

            @keyframes messageSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .susan-message.user {
                align-self: flex-end;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-bottom-right-radius: 6px;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }

            .susan-message.assistant {
                align-self: flex-start;
                background: white;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-bottom-left-radius: 6px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }

            .susan-message.assistant::before {
                content: '🤖';
                position: absolute;
                left: -8px;
                top: -8px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                border: 2px solid white;
            }

            .susan-typing.enhanced {
                padding: 12px 20px;
                display: flex;
                align-items: center;
                gap: 12px;
                background: #f8fafc;
                border-top: 1px solid #e5e7eb;
            }

            .susan-typing-avatar {
                width: 32px;
                height: 32px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }

            .susan-typing-indicator {
                display: flex;
                gap: 4px;
                margin-bottom: 4px;
            }

            .susan-typing-indicator span {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #9ca3af;
                animation: typing 1.4s infinite ease-in-out;
            }

            .susan-typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
            .susan-typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

            @keyframes typing {
                0%, 80%, 100% {
                    transform: scale(0.8);
                    opacity: 0.5;
                }
                40% {
                    transform: scale(1);
                    opacity: 1;
                }
            }

            .susan-typing-text {
                font-size: 12px;
                color: #6b7280;
                font-style: italic;
            }

            .susan-suggestions {
                padding: 8px 20px;
                background: #f8fafc;
                border-top: 1px solid #e5e7eb;
                display: none;
            }

            .susan-suggestions.active {
                display: block;
            }

            .suggestion-chip {
                display: inline-block;
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                padding: 6px 12px;
                margin: 4px 4px 4px 0;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                color: #374151;
            }

            .suggestion-chip:hover {
                background: #667eea;
                color: white;
                border-color: #667eea;
                transform: translateY(-1px);
            }

            .susan-input-area.enhanced {
                padding: 16px 20px;
                background: white;
                border-top: 1px solid #e5e7eb;
                border-radius: 0 0 20px 20px;
            }

            .susan-quick-actions {
                display: flex;
                gap: 8px;
                margin-bottom: 12px;
                flex-wrap: wrap;
            }

            .susan-quick-btn {
                background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
                border: 1px solid #d1d5db;
                color: #374151;
                padding: 8px 12px;
                border-radius: 12px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 6px;
                white-space: nowrap;
            }

            .susan-quick-btn:hover {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-color: #667eea;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }

            .susan-quick-btn.conversation {
                border-color: #10b981;
                color: #059669;
            }

            .susan-quick-btn.conversation:hover {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                border-color: #10b981;
            }

            .susan-quick-btn.official {
                border-color: #f59e0b;
                color: #d97706;
            }

            .susan-quick-btn.official:hover {
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                border-color: #f59e0b;
            }

            .susan-input-container {
                display: flex;
                gap: 12px;
                align-items: flex-end;
            }

            .susan-input.enhanced {
                flex: 1;
                border: 2px solid #e5e7eb;
                border-radius: 14px;
                padding: 12px 16px;
                font-size: 14px;
                outline: none;
                transition: all 0.3s ease;
                background: #f9fafb;
                resize: none;
                min-height: 44px;
                max-height: 120px;
            }

            .susan-input.enhanced:focus {
                border-color: #667eea;
                background: white;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            .susan-send-btn.enhanced {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                color: white;
                width: 44px;
                height: 44px;
                border-radius: 12px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                transition: all 0.2s ease;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }

            .susan-send-btn.enhanced:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
            }

            .susan-send-btn.enhanced:active {
                transform: translateY(0);
            }

            .susan-input-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 8px;
                font-size: 11px;
                color: #9ca3af;
            }

            .character-count {
                font-weight: 500;
            }

            .susan-help-hint {
                font-style: italic;
            }

            /* Mobile responsiveness */
            @media (max-width: 768px) {
                .susan-chat.enhanced {
                    width: 320px;
                    height: 500px;
                    right: 10px;
                    bottom: 70px;
                }

                .susan-assistant.enhanced {
                    bottom: 15px;
                    right: 15px;
                }

                .susan-toggle.enhanced {
                    width: 60px;
                    height: 60px;
                }

                .susan-quick-actions {
                    gap: 6px;
                }

                .susan-quick-btn {
                    padding: 6px 10px;
                    font-size: 11px;
                }
            }

            /* Accessibility improvements */
            .susan-toggle.enhanced:focus,
            .susan-control-btn:focus,
            .susan-send-btn.enhanced:focus,
            .susan-input.enhanced:focus {
                outline: 2px solid #667eea;
                outline-offset: 2px;
            }

            /* Custom scrollbar */
            .susan-messages.enhanced::-webkit-scrollbar {
                width: 6px;
            }

            .susan-messages.enhanced::-webkit-scrollbar-track {
                background: #f1f5f9;
                border-radius: 3px;
            }

            .susan-messages.enhanced::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 3px;
            }

            .susan-messages.enhanced::-webkit-scrollbar-thumb:hover {
                background: #94a3b8;
            }
        `;
        document.head.appendChild(style);
    }

    bindEvents() {
        // Toggle chat
        document.getElementById('susan-toggle').addEventListener('click', () => {
            this.toggleChat();
        });

        // Close and minimize
        document.getElementById('susan-close').addEventListener('click', () => {
            this.closeChat();
        });

        document.getElementById('susan-minimize').addEventListener('click', () => {
            this.closeChat();
        });

        // Send message
        document.getElementById('susan-send').addEventListener('click', () => {
            this.sendMessage();
        });

        // Enhanced input handling
        const input = document.getElementById('susan-input');
        
        // Enter to send, Shift+Enter for new line
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Character counter
        input.addEventListener('input', (e) => {
            const count = e.target.value.length;
            document.getElementById('character-count').textContent = `${count}/500`;
            
            // Update input height for multiline
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
        });

        // Quick action buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('susan-quick-btn')) {
                const message = e.target.getAttribute('data-message');
                this.sendQuickMessage(message);
            }
        });

        // Suggestion chips
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-chip')) {
                const message = e.target.textContent;
                this.sendQuickMessage(message);
            }
        });

        // ESC to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeChat();
            }
        });

        // Mood button
        document.getElementById('susan-mood-btn').addEventListener('click', () => {
            this.showMoodInfo();
        });
    }

    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        const chatElement = document.getElementById('susan-chat');
        chatElement.classList.add('open');
        this.isOpen = true;
        
        // Focus input with delay
        setTimeout(() => {
            const input = document.getElementById('susan-input');
            if (input) {
                input.focus();
            }
        }, 300);

        // Hide tooltip
        const tooltip = document.querySelector('.susan-tooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }

        // Update suggestions based on context
        this.updateSuggestions();
    }

    closeChat() {
        const chatElement = document.getElementById('susan-chat');
        chatElement.classList.remove('open');
        this.isOpen = false;

        // Show tooltip again
        const tooltip = document.querySelector('.susan-tooltip');
        if (tooltip) {
            tooltip.style.display = 'block';
        }
    }

    async loadPersonalizedWelcome() {
        // Load conversation memory first
        await this.loadConversationMemory();
        
        // Add personalized welcome message
        setTimeout(() => {
            let welcomeMessage;
            const hour = new Date().getHours();
            const timeGreeting = hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening';
            
            if (this.conversationMemory.has('hasInteracted')) {
                welcomeMessage = `Good ${timeGreeting}! 😊 Welcome back! I'm here and ready to chat or help with Sports Schedulers. What's on your mind today?`;
            } else {
                welcomeMessage = `Good ${timeGreeting}! 👋 I'm Susan, your friendly Sports Schedulers assistant! I love having conversations and helping people succeed. Click me anytime you want to chat!`;
                this.conversationMemory.set('hasInteracted', true);
            }
            
            // Don't auto-add if chat is already open
            if (!this.isOpen) {
                this.updateStatusText("Click to chat! 💬");
            }
        }, 2000);
    }

    async initializeConversationMemory() {
        try {
            const response = await fetch('/api/assistant/memory');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Load user's conversation history
                    this.conversationMemory.set('topics', data.memory.topics_discussed || []);
                    this.conversationMemory.set('preferences', data.memory.preferences || {});
                    this.conversationMemory.set('lastSeen', data.memory.last_seen);
                }
            }
        } catch (error) {
            console.log('Could not load conversation memory:', error);
        }
    }

    async loadConversationMemory() {
        // This would typically load from localStorage or API
        // For now, we'll use simple session storage
        const memory = sessionStorage.getItem('susan_memory');
        if (memory) {
            const parsed = JSON.parse(memory);
            for (const [key, value] of Object.entries(parsed)) {
                this.conversationMemory.set(key, value);
            }
        }
    }

    saveConversationMemory() {
        const memoryObj = {};
        for (const [key, value] of this.conversationMemory.entries()) {
            memoryObj[key] = value;
        }
        sessionStorage.setItem('susan_memory', JSON.stringify(memoryObj));
    }

    sendMessage() {
        const input = document.getElementById('susan-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message
        this.addMessage('user', message);
        
        // Clear input and reset height
        input.value = '';
        input.style.height = 'auto';
        document.getElementById('character-count').textContent = '0/500';
        
        // Hide suggestions
        this.hideSuggestions();
        
        // Show typing indicator
        this.showTyping();
        
        // Process message
        this.processMessage(message);
    }

    sendQuickMessage(message) {
        if (!message) return;

        // Add user message
        this.addMessage('user', message);
        
        // Hide suggestions
        this.hideSuggestions();
        
        // Show typing indicator
        this.showTyping();
        
        // Process message
        this.processMessage(message);
    }

    addMessage(sender, content) {
        const messagesContainer = document.getElementById('susan-messages');
        const messageElement = document.createElement('div');
        messageElement.className = `susan-message ${sender}`;
        
        // Format content for display
        const formattedContent = this.formatMessage(content);
        messageElement.innerHTML = formattedContent;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Add to messages array
        this.messages.push({ sender, content, timestamp: new Date() });
        
        // Update mood based on message
        if (sender === 'assistant') {
            this.updateMoodBasedOnMessage(content);
        }
    }

    formatMessage(text) {
        // Enhanced message formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic
            .replace(/`(.*?)`/g, '<code style="background: #f3f4f6; padding: 2px 4px; border-radius: 4px; font-family: monospace;">$1</code>')  // Code
            .replace(/\n/g, '<br>')                           // Line breaks
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color: #667eea; text-decoration: underline;">$1</a>'); // Links
    }

    async processMessage(message) {
        // Update conversation context
        this.updateConversationContext(message);
        
        try {
            const response = await fetch('/api/assistant/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message,
                    context: {
                        page: this.currentPage,
                        userType: this.currentPage === 'official' ? 'official' : 'admin',
                        conversationContext: this.conversationContext,
                        emotionalState: this.conversationContext.emotionalState
                    }
                })
            });

            const data = await response.json();
            
            // Hide typing indicator
            this.hideTyping();

            if (data.success) {
                // Add Susan's response with enhanced formatting
                this.addMessage('assistant', data.response);
                
                // Update suggestions based on response
                this.generateContextualSuggestions(data.response);
                
                // Update status
                this.updateStatusText("Online and chatting! 😊");
                
            } else {
                this.addMessage('assistant', "I'm having a little trouble right now! 😅 Could you try that again? I'm usually much more reliable than this!");
            }
        } catch (error) {
            this.hideTyping();
            this.addMessage('assistant', "Oops! Looks like I'm having connection issues! 📡 Please check your internet and try again. I'll be here waiting! 💙");
            console.error('Susan chat error:', error);
        }
        
        // Save conversation memory
        this.saveConversationMemory();
    }

    updateConversationContext(message) {
        const lowerMessage = message.toLowerCase();
        
        // Detect emotional state
        if (lowerMessage.includes('frustrated') || lowerMessage.includes('confused') || lowerMessage.includes('help')) {
            this.conversationContext.emotionalState = 'needs_support';
        } else if (lowerMessage.includes('thank') || lowerMessage.includes('great') || lowerMessage.includes('awesome')) {
            this.conversationContext.emotionalState = 'positive';
        } else if (lowerMessage.includes('hi') || lowerMessage.includes('hello') || lowerMessage.includes('hey')) {
            this.conversationContext.emotionalState = 'greeting';
        } else {
            this.conversationContext.emotionalState = 'neutral';
        }
        
        // Detect topic
        if (lowerMessage.includes('game') || lowerMessage.includes('schedule')) {
            this.conversationContext.lastTopic = 'games';
        } else if (lowerMessage.includes('official') || lowerMessage.includes('assign')) {
            this.conversationContext.lastTopic = 'officials';
        } else if (lowerMessage.includes('help') || lowerMessage.includes('how')) {
            this.conversationContext.lastTopic = 'help';
        }
    }

    generateContextualSuggestions(response) {
        const suggestions = [];
        const responseLower = response.toLowerCase();
        
        // Generate suggestions based on Susan's response
        if (responseLower.includes('game')) {
            suggestions.push('How do I add games?', 'Tell me about CSV import', 'Show me game management tips');
        }
        if (responseLower.includes('official')) {
            suggestions.push('Help with assignments', 'Managing official profiles', 'Availability settings');
        }
        if (responseLower.includes('joke') || responseLower.includes('fun')) {
            suggestions.push('Tell me another joke!', 'What else is fun about scheduling?', 'Any sports trivia?');
        }
        if (responseLower.includes('help')) {
            suggestions.push('What else can you help with?', 'Show me advanced features', 'Best practices tips');
        }
        
        // Always include some conversational options
        suggestions.push('How are you doing, Susan?', 'Thanks for the help!');
        
        this.showSuggestions(suggestions.slice(0, 4)); // Show max 4 suggestions
    }

    showSuggestions(suggestions) {
        const suggestionsContainer = document.getElementById('susan-suggestions');
        
        if (suggestions && suggestions.length > 0) {
            suggestionsContainer.innerHTML = suggestions
                .map(suggestion => `<span class="suggestion-chip">${suggestion}</span>`)
                .join('');
            suggestionsContainer.classList.add('active');
        }
    }

    hideSuggestions() {
        const suggestionsContainer = document.getElementById('susan-suggestions');
        suggestionsContainer.classList.remove('active');
    }

    updateSuggestions() {
        // Context-aware suggestions when opening chat
        let suggestions = [];
        
        if (this.currentPage === 'official') {
            suggestions = [
                'Hi Susan! How are you?',
                'Help with my games',
                'How do I set availability?',
                'Tell me a joke!'
            ];
        } else {
            suggestions = [
                'Hi Susan! How are you?',
                'Help me add games',
                'Show me official management',
                'What can you do?'
            ];
        }
        
        this.showSuggestions(suggestions);
    }

    updateMoodBasedOnMessage(content) {
        const contentLower = content.toLowerCase();
        const moodIndicator = document.getElementById('susan-mood');
        const moodBtn = document.getElementById('susan-mood-btn');
        
        let mood = '😊'; // default
        
        if (contentLower.includes('excited') || contentLower.includes('amazing') || contentLower.includes('awesome')) {
            mood = '🤩';
        } else if (contentLower.includes('help') || contentLower.includes('guide')) {
            mood = '🤓';
        } else if (contentLower.includes('joke') || contentLower.includes('fun') || contentLower.includes('laugh')) {
            mood = '😄';
        } else if (contentLower.includes('sorry') || contentLower.includes('trouble')) {
            mood = '😅';
        } else if (contentLower.includes('love') || contentLower.includes('enjoy')) {
            mood = '🥰';
        }
        
        if (moodIndicator) moodIndicator.textContent = mood;
        if (moodBtn) moodBtn.textContent = mood;
    }

    updateStatusText(text) {
        const statusElement = document.getElementById('susan-status');
        if (statusElement) {
            statusElement.textContent = text;
        }
    }

    showMoodInfo() {
        // Simple mood explanation
        const moods = {
            '😊': 'I\'m feeling friendly and helpful!',
            '🤩': 'I\'m super excited to help you!',
            '🤓': 'I\'m in teaching mode - ready to help you learn!',
            '😄': 'I\'m in a playful mood!',
            '😅': 'I\'m a bit embarrassed, but still here to help!',
            '🥰': 'I\'m feeling warm and caring!'
        };
        
        const currentMood = document.getElementById('susan-mood').textContent;
        const explanation = moods[currentMood] || 'I\'m feeling good and ready to chat!';
        
        this.addMessage('assistant', `${currentMood} ${explanation} What would you like to talk about?`);
    }

    showTyping() {
        document.getElementById('susan-typing').style.display = 'flex';
        const messagesContainer = document.getElementById('susan-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Update status
        this.updateStatusText("Thinking... 🤔");
        
        // Randomize typing duration for more natural feel
        const typingDuration = Math.random() * 1000 + 1500; // 1.5-2.5 seconds
        
        setTimeout(() => {
            this.updateStatusText("Crafting response... ✨");
        }, typingDuration * 0.6);
    }

    hideTyping() {
        document.getElementById('susan-typing').style.display = 'none';
        this.updateStatusText("Online and ready to chat! 😊");
    }

    // Enhanced accessibility methods
    announceMessage(message) {
        // Screen reader announcement
        if (window.speechSynthesis && this.userPreferences.screenReader) {
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.rate = 0.8;
            utterance.pitch = 1.1;
            window.speechSynthesis.speak(utterance);
        }
    }

    // Conversation management
    clearConversation() {
        this.messages = [];
        const messagesContainer = document.getElementById('susan-messages');
        messagesContainer.innerHTML = '';
        
        // Add fresh welcome message
        setTimeout(() => {
            this.addMessage('assistant', "Hi again! 👋 Fresh start! What would you like to chat about?");
        }, 500);
    }

    exportConversation() {
        const conversation = this.messages.map(msg => 
            `[${msg.timestamp.toLocaleString()}] ${msg.sender}: ${msg.content}`
        ).join('\n');
        
        const blob = new Blob([conversation], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `susan-conversation-${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // Public API methods for external integration
    sendProgrammaticMessage(message) {
        if (!this.isOpen) {
            this.openChat();
        }
        
        setTimeout(() => {
            this.sendQuickMessage(message);
        }, 300);
    }

    setUserPreference(key, value) {
        this.userPreferences[key] = value;
        this.saveConversationMemory();
    }

    getUserPreference(key) {
        return this.userPreferences[key];
    }

    // Context-aware help launcher
    launchContextualHelp(topic) {
        const helpMessages = {
            'games': 'I noticed you might need help with games! I can guide you through adding games, importing CSV files, and managing schedules. What specifically would you like to know?',
            'officials': 'Let me help you with officials management! I can show you how to add officials, manage their profiles, set availability, and make assignments. What would you like to start with?',
            'assignments': 'Assignment time! 🎯 I can help you assign officials to games, manage their responses, and track everything smoothly. What do you need help with?',
            'reports': 'Reports and analytics! 📊 I can guide you through generating reports, understanding your data, and getting insights. What kind of report interests you?'
        };
        
        const message = helpMessages[topic] || `I'm here to help you with ${topic}! What would you like to know?`;
        
        if (!this.isOpen) {
            this.openChat();
        }
        
        setTimeout(() => {
            this.addMessage('assistant', message);
            this.updateSuggestions();
        }, 300);
    }
}

// Initialize Enhanced Susan when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Susan for all users except login page
    const isLoginPage = window.location.pathname === '/login';
    
    if (!isLoginPage) {
        // Slight delay to ensure page is fully loaded
        setTimeout(() => {
            window.susanAssistant = new EnhancedSusanAssistant();
            
            // Add global helper functions
            window.susanHelp = {
                games: () => window.susanAssistant.launchContextualHelp('games'),
                officials: () => window.susanAssistant.launchContextualHelp('officials'),
                assignments: () => window.susanAssistant.launchContextualHelp('assignments'),
                reports: () => window.susanAssistant.launchContextualHelp('reports'),
                chat: (message) => window.susanAssistant.sendProgrammaticMessage(message)
            };
            
            // Expose for debugging and external integration
            window.Susan = window.susanAssistant;
            
        }, 1000);
    }
});

// Export for manual initialization if needed
window.EnhancedSusanAssistant = EnhancedSusanAssistant;