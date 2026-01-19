document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const questionForm = document.getElementById('question-form');
    const questionInput = document.getElementById('question-input');
    const sendBtn = document.getElementById('send-btn');
    const quickQuestions = document.querySelectorAll('.quick-question');

    // Check system status on load
    checkHealth();

    // Form submit handler
    questionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (question) {
            askQuestion(question);
            questionInput.value = '';
        }
    });

    // Quick question buttons
    quickQuestions.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const question = this.dataset.question;
            questionInput.value = question;
            askQuestion(question);
            questionInput.value = '';
        });
    });

    function askQuestion(question) {
        // Remove welcome message if present
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        // Add user message
        addMessage(question, 'user');

        // Show typing indicator
        const typingId = showTypingIndicator();

        // Disable input while processing
        setInputState(false);

        // Send to API
        fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator(typingId);

            if (data.error) {
                addMessage(data.answer || data.error, 'assistant', { error: true });
            } else {
                addMessage(data.answer, 'assistant', {
                    intent: data.intent,
                    queryExecuted: data.query_executed,
                    rowCount: data.row_count
                });
            }
        })
        .catch(error => {
            removeTypingIndicator(typingId);
            addMessage('Bir hata olustu. Lutfen tekrar deneyin.', 'assistant', { error: true });
            console.error('Error:', error);
        })
        .finally(() => {
            setInputState(true);
            questionInput.focus();
        });
    }

    function addMessage(content, type, meta = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (meta.error) {
            contentDiv.classList.add('error-message');
        }

        // Parse markdown for assistant messages
        if (type === 'assistant' && typeof marked !== 'undefined') {
            contentDiv.innerHTML = marked.parse(content);
        } else {
            contentDiv.textContent = content;
        }

        messageDiv.appendChild(contentDiv);

        // Add meta info for assistant messages
        if (type === 'assistant' && !meta.error) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';

            let metaText = '';
            if (meta.intent && meta.intent !== 'general') {
                metaText += `<span class="intent-badge">${formatIntent(meta.intent)}</span>`;
            }
            if (meta.queryExecuted && meta.rowCount !== undefined) {
                metaText += ` <small>${meta.rowCount} kayit</small>`;
            }

            if (metaText) {
                metaDiv.innerHTML = metaText;
                messageDiv.appendChild(metaDiv);
            }
        }

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.id = id;
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
        return id;
    }

    function removeTypingIndicator(id) {
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    }

    function setInputState(enabled) {
        questionInput.disabled = !enabled;
        sendBtn.disabled = !enabled;
        if (enabled) {
            sendBtn.innerHTML = '<i class="bi bi-send"></i>';
        } else {
            sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatIntent(intent) {
        const labels = {
            'concurrent_manager': 'Concurrent Manager',
            'workflow': 'Workflow',
            'invalid_objects': 'Invalid Objects',
            'tablespace': 'Tablespace',
            'concurrent_requests': 'Requests',
            'alerts': 'Alerts'
        };
        return labels[intent] || intent;
    }

    function checkHealth() {
        fetch('/api/health')
            .then(response => response.json())
            .then(data => {
                const dbStatus = document.getElementById('db-status');
                const llmStatus = document.getElementById('llm-status');

                if (data.database === 'connected') {
                    dbStatus.classList.add('connected');
                } else {
                    dbStatus.classList.add('warning');
                }

                if (data.llm === 'configured') {
                    llmStatus.classList.add('connected');
                } else {
                    llmStatus.classList.add('warning');
                }
            })
            .catch(() => {
                // Silent fail for health check
            });
    }
});
