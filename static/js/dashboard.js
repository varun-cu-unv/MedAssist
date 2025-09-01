// Chat History Management
let chatSessions = [];
let currentSessionId = null;

// Initialize chat history from localStorage
function initializeChatHistory() {
    const savedSessions = localStorage.getItem('medassist_chat_sessions');
    if (savedSessions) {
        chatSessions = JSON.parse(savedSessions);
    }
    
    if (chatSessions.length === 0) {
        startNewChat();
    } else {
        loadChatSession(chatSessions[0].id);
    }
    
    renderChatSessions();
}

// Save chat sessions to localStorage
function saveChatSessions() {
    localStorage.setItem('medassist_chat_sessions', JSON.stringify(chatSessions));
}

// Generate unique ID for chat sessions
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Start a new chat session
function startNewChat() {
    const newSession = {
        id: generateSessionId(),
        title: 'New Chat',
        messages: [{
            type: 'bot',
            content: "Hello! I'm your AI health assistant. How can I help you today?",
            timestamp: new Date().toISOString()
        }],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    
    chatSessions.unshift(newSession);
    currentSessionId = newSession.id;
    saveChatSessions();
    renderChatSessions();
    loadChatSession(newSession.id);
}

// Load a specific chat session
function loadChatSession(sessionId) {
    const session = chatSessions.find(s => s.id === sessionId);
    if (!session) return;
    
    currentSessionId = sessionId;
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // Clear current messages
    chatMessages.innerHTML = '';
    
    // Load session messages
    session.messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = msg.type === 'bot' ? 'bot-message' : 'user-message';
        
        if (msg.type === 'bot') {
            messageDiv.innerHTML = `
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <p>${msg.content}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p>${msg.content}</p>
                </div>
                <div class="message-avatar">👤</div>
            `;
        }
        
        chatMessages.appendChild(messageDiv);
    });
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
    renderChatSessions();
}

// Delete a chat session
function deleteChatSession(sessionId) {
    if (chatSessions.length <= 1) {
        alert("You must have at least one chat session!");
        return;
    }
    
    if (!confirm("Are you sure you want to delete this chat?")) {
        return;
    }
    
    chatSessions = chatSessions.filter(s => s.id !== sessionId);
    
    if (currentSessionId === sessionId) {
        currentSessionId = chatSessions[0].id;
        loadChatSession(currentSessionId);
    }
    
    saveChatSessions();
    renderChatSessions();
}

// Rename a chat session
function renameChatSession(sessionId) {
    const session = chatSessions.find(s => s.id === sessionId);
    if (!session) return;
    
    const newTitle = prompt("Enter new chat name:", session.title);
    if (newTitle && newTitle.trim()) {
        session.title = newTitle.trim();
        session.updatedAt = new Date().toISOString();
        saveChatSessions();
        renderChatSessions();
    }
}

// Clear all chat sessions
function clearAllChats() {
    if (!confirm("Are you sure you want to delete all chat history? This action cannot be undone.")) {
        return;
    }
    
    chatSessions = [];
    localStorage.removeItem('medassist_chat_sessions');
    startNewChat();
}

// Export chat history
function exportChatHistory() {
    const dataStr = JSON.stringify(chatSessions, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'medassist_chat_history.json';
    link.click();
}

// Render chat sessions in sidebar
function renderChatSessions() {
    const chatSessionsContainer = document.getElementById('chatSessions');
    if (!chatSessionsContainer) return;
    
    chatSessionsContainer.innerHTML = '';
    
    chatSessions.forEach(session => {
        const sessionDiv = document.createElement('div');
        sessionDiv.className = `chat-session ${session.id === currentSessionId ? 'active' : ''}`;
        sessionDiv.onclick = () => loadChatSession(session.id);
        
        const lastMessage = session.messages[session.messages.length - 1];
        const preview = lastMessage ? lastMessage.content.substring(0, 50) + '...' : 'No messages';
        const timeStr = new Date(session.updatedAt).toLocaleDateString();
        
        sessionDiv.innerHTML = `
            <div class="chat-session-header">
                <div class="chat-session-title">${session.title}</div>
                <div class="chat-session-time">${timeStr}</div>
            </div>
            <div class="chat-session-preview">${preview}</div>
            <div class="chat-session-actions">
                <button class="chat-action-btn" onclick="event.stopPropagation(); renameChatSession('${session.id}')" title="Rename">
                    ✏️
                </button>
                <button class="chat-action-btn delete-btn" onclick="event.stopPropagation(); deleteChatSession('${session.id}')" title="Delete">
                    🗑️
                </button>
            </div>
        `;
        
        chatSessionsContainer.appendChild(sessionDiv);
    });
}

// Update session title based on first user message
function updateSessionTitle(sessionId, userMessage) {
    const session = chatSessions.find(s => s.id === sessionId);
    if (!session || session.title !== 'New Chat') return;
    
    // Generate title from first few words of user message
    const words = userMessage.split(' ').slice(0, 4).join(' ');
    session.title = words.length > 30 ? words.substring(0, 30) + '...' : words;
    session.updatedAt = new Date().toISOString();
    saveChatSessions();
    renderChatSessions();
}

// Enhanced send message function
function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    
    if (!chatInput || !chatMessages || !chatInput.value.trim()) return;
    
    const userMessage = chatInput.value.trim();
    const currentSession = chatSessions.find(s => s.id === currentSessionId);
    if (!currentSession) return;
    
    // Add user message to session
    currentSession.messages.push({
        type: 'user',
        content: userMessage,
        timestamp: new Date().toISOString()
    });
    
    // Update session title if it's a new chat
    if (currentSession.messages.length === 2) { // Bot greeting + first user message
        updateSessionTitle(currentSessionId, userMessage);
    }
    
    // Add user message to UI
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'user-message';
    userMessageDiv.innerHTML = `
        <div class="message-content">
            <p>${userMessage}</p>
        </div>
        <div class="message-avatar">👤</div>
    `;
    chatMessages.appendChild(userMessageDiv);
    
    // Clear input
    chatInput.value = '';
    
    // Simulate bot response
    setTimeout(() => {
        const botResponse = getBotResponse(userMessage);
        
        // Add bot message to session
        currentSession.messages.push({
            type: 'bot',
            content: botResponse,
            timestamp: new Date().toISOString()
        });
        
        currentSession.updatedAt = new Date().toISOString();
        saveChatSessions();
        renderChatSessions();
        
        // Add bot message to UI
        const botMessageDiv = document.createElement('div');
        botMessageDiv.className = 'bot-message';
        botMessageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <p>${botResponse}</p>
            </div>
        `;
        chatMessages.appendChild(botMessageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 1000);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Enhanced bot responses
function getBotResponse(message) {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('pain') || lowerMessage.includes('hurt')) {
        return "I understand you're experiencing pain. It's important to consult with a healthcare professional for proper diagnosis and treatment. In the meantime, rest and avoid activities that worsen the pain.";
    }
    
    if (lowerMessage.includes('medication') || lowerMessage.includes('medicine')) {
        return "For medication-related questions, please consult your doctor or pharmacist. They can provide guidance on dosage, side effects, and interactions based on your specific health profile.";
    }
    
    if (lowerMessage.includes('appointment') || lowerMessage.includes('schedule')) {
        return "I can help you understand when to seek medical care. Would you like me to provide information about preparing for your appointment or what questions to ask your doctor?";
    }
    
    if (lowerMessage.includes('symptom')) {
        return "I can provide general health information, but for specific symptoms, it's best to consult with a healthcare professional. They can properly evaluate your condition and recommend appropriate care.";
    }
    
    const responses = [
        "I'm here to provide general health information and support. How can I assist you with your health-related questions today?",
        "That's a thoughtful question. For personalized medical advice, please consult with your healthcare provider.",
        "I understand your concern. Let me provide some general information that might be helpful, but always verify with a medical professional.",
        "Thank you for reaching out. I'm here to help with health information and guidance. What specific area would you like to learn more about?",
        "I'm designed to provide helpful health information. For the most accurate and personalized advice, consulting with your doctor is always recommended."
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
}

// Theme toggle functionality
function toggleTheme() {
    const body = document.body;
    const themeBtn = document.querySelector('.theme-toggle');

    if (!body || !themeBtn) return;

    body.classList.toggle('light-mode');

    if (body.classList.contains('light-mode')) {
        themeBtn.textContent = '☀️';
        localStorage.setItem('theme', 'light');
    } else {
        themeBtn.textContent = '🌙';
        localStorage.setItem('theme', 'dark');
    }
}

// Load saved theme
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme');
    const body = document.body;
    const themeBtn = document.querySelector('.theme-toggle');

    if (!body || !themeBtn) return;

    if (savedTheme === 'light') {
        body.classList.add('light-mode');
        themeBtn.textContent = '☀️';
    } else {
        themeBtn.textContent = '🌙';
    }
}

// Chatbot toggle functionality
function toggleChatbot() {
    const chatContent = document.getElementById('chatbotContent');
    const toggleIcon = document.getElementById('chatToggleIcon');
    
    if (chatContent && toggleIcon) {
        chatContent.classList.toggle('collapsed');
        toggleIcon.textContent = chatContent.classList.contains('collapsed') ? '➕' : '➖';
    }
}

// Action button functions
function toggleVoiceCommand() {
    alert('Voice Command feature coming soon! Stay tuned for updates.');
}

function openAppointments() {
    alert('Appointment booking system will be available soon. Please call your healthcare provider for now.');
}

function toggleMultilingual() {
    alert('Multilingual support coming soon! Currently available in English.');
}

function openAboutUs() {
    alert('About Us: MedAssist is your AI-powered health companion, designed to help you manage your wellness journey with intelligent insights and personalized care.');
}

function confirmLogout() {
    if (confirm('Are you sure you want to logout?')) {
        document.getElementById('logoutForm').submit();
    }
}

// Chat input Enter key support
function setupChatInput() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
}

// Initialize dashboard
function initializeDashboard() {
    try {
        loadSavedTheme();
        setupChatInput();
        initializeChatHistory();
        
        if (document.documentElement) {
            document.documentElement.style.scrollBehavior = 'smooth';
        }
    } catch (error) {
        console.error('Dashboard initialization error:', error);
    }
}

function openHealthRecords() {
    window.location.href = '/health-records';
}

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

// Make functions globally available
window.toggleTheme = toggleTheme;
window.toggleChatbot = toggleChatbot;
window.sendMessage = sendMessage;
window.startNewChat = startNewChat;
window.clearAllChats = clearAllChats;
window.exportChatHistory = exportChatHistory;
window.toggleVoiceCommand = toggleVoiceCommand;
window.openAppointments = openAppointments;
window.toggleMultilingual = toggleMultilingual;
window.openAboutUs = openAboutUs;
window.confirmLogout = confirmLogout;

// Chat input Enter key support
function setupChatInput() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
}

// Initialize dashboard
function initializeDashboard() {
    try {
        // Load theme
        loadSavedTheme();
        
        // Setup chat input
        setupChatInput();
        
        // Add smooth scroll
        if (document.documentElement) {
            document.documentElement.style.scrollBehavior = 'smooth';
        }
    } catch (error) {
        console.error('Dashboard initialization error:', error);
    }
}

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

// Make functions globally available
window.toggleTheme = toggleTheme;
window.toggleChatbot = toggleChatbot;
window.sendMessage = sendMessage;
window.toggleVoiceCommand = toggleVoiceCommand;
window.openAppointments = openAppointments;
window.toggleMultilingual = toggleMultilingual;
window.openAboutUs = openAboutUs;
window.confirmLogout = confirmLogout;
window.openHealthMetrics = openHealthMetrics;
window.openMedications = openMedications;
window.openReports = openReports;
window.openEmergency = openEmergency;