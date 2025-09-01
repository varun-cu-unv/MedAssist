// voice-recorder.js - Advanced voice recording functionality
class VoiceRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.stream = null;
        this.recognition = null;
        
        this.initializeSpeechRecognition();
    }
    
    // Initialize Web Speech API (browser-based recognition)
    initializeSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.maxAlternatives = 1;
            
            // Event handlers
            this.recognition.onstart = () => {
                this.onRecordingStart();
            };
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                const confidence = event.results[0][0].confidence;
                this.onTranscriptionComplete(transcript, confidence);
            };
            
            this.recognition.onerror = (event) => {
                this.onRecordingError(event.error);
            };
            
            this.recognition.onend = () => {
                this.onRecordingEnd();
            };
        }
    }
    
    // Start recording using Web Speech API (preferred method)
    async startSpeechRecognition(language = 'en-US') {
        if (!this.recognition) {
            throw new Error('Speech recognition not supported');
        }
        
        this.recognition.lang = language;
        
        try {
            this.recognition.start();
        } catch (error) {
            if (error.name === 'InvalidStateError') {
                this.recognition.stop();
                setTimeout(() => this.recognition.start(), 100);
            } else {
                throw error;
            }
        }
    }
    
    // Start recording using MediaRecorder API (for server-side processing)
    async startMediaRecording() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                }
            });
            
            this.audioChunks = [];
            
            // Use appropriate MIME type
            const options = this.getSupportedMimeType();
            this.mediaRecorder = new MediaRecorder(this.stream, options);
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecordedAudio();
            };
            
            this.mediaRecorder.onerror = (event) => {
                this.onRecordingError(event.error);
            };
            
            this.mediaRecorder.start(1000); // Collect data every second
            this.onRecordingStart();
            
        } catch (error) {
            if (error.name === 'NotAllowedError') {
                throw new Error('Microphone permission denied. Please allow microphone access and try again.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No microphone found. Please connect a microphone and try again.');
            } else {
                throw new Error(`Recording failed: ${error.message}`);
            }
        }
    }
    
    // Stop current recording
    stopRecording() {
        if (this.recognition && this.isRecording) {
            this.recognition.stop();
        }
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }
    
    // Process recorded audio blob
    async processRecordedAudio() {
        if (this.audioChunks.length === 0) {
            this.onRecordingError('No audio data recorded');
            return;
        }
        
        const audioBlob = new Blob(this.audioChunks, { 
            type: this.getSupportedMimeType().type 
        });
        
        // Convert to base64 for sending to server
        const base64Audio = await this.blobToBase64(audioBlob);
        
        // Send to server for processing
        this.sendAudioToServer(base64Audio);
    }
    
    // Convert blob to base64
    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    // Send audio to server for processing
    async sendAudioToServer(audioData) {
        try {
            const response = await fetch('/process-voice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    audio_data: audioData,
                    language: this.getCurrentLanguage()
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.onTranscriptionComplete(result.transcript, 1.0);
            } else {
                this.onRecordingError(result.error || 'Transcription failed');
            }
            
        } catch (error) {
            this.onRecordingError(`Network error: ${error.message}`);
        }
    }
    
    // Get supported MIME type for recording
    getSupportedMimeType() {
        const mimeTypes = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/mpeg',
            'audio/wav'
        ];
        
        for (const mimeType of mimeTypes) {
            if (MediaRecorder.isTypeSupported(mimeType)) {
                return { type: mimeType };
            }
        }
        
        return {}; // Use default
    }
    
    // Get current language setting
    getCurrentLanguage() {
        const languageSelect = document.getElementById('languageSelect');
        return languageSelect ? languageSelect.value : 'en';
    }
    
    // Get speech recognition language code
    getSpeechLanguageCode(langCode) {
        const languageMap = {
            'en': 'en-US',
            'hi': 'hi-IN',
            'ta': 'ta-IN',
            'te': 'te-IN',
            'kn': 'kn-IN',
            'ml': 'ml-IN',
            'gu': 'gu-IN',
            'bn': 'bn-IN',
            'mr': 'mr-IN',
            'pa': 'pa-IN',
            'ur': 'ur-IN',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'zh': 'zh-CN',
            'ar': 'ar-SA'
        };
        
        return languageMap[langCode] || 'en-US';
    }
    
    // Event handlers (to be overridden)
    onRecordingStart() {
        this.isRecording = true;
        console.log('Recording started');
    }
    
    onRecordingEnd() {
        this.isRecording = false;
        console.log('Recording ended');
    }
    
    onTranscriptionComplete(transcript, confidence) {
        console.log('Transcription:', transcript, 'Confidence:', confidence);
    }
    
    onRecordingError(error) {
        this.isRecording = false;
        console.error('Recording error:', error);
    }
}

// Enhanced UI controller for the chatbot
class ChatbotUIController {
    constructor() {
        this.voiceRecorder = new VoiceRecorder();
        this.currentLanguage = 'en';
        this.isProcessing = false;
        
        this.initializeElements();
        this.setupEventHandlers();
        this.setupVoiceRecorder();
    }
    
    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.drugInput = document.getElementById('drugInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.micButton = document.getElementById('micButton');
        this.voiceStatus = document.getElementById('voiceStatus');
        this.languageSelect = document.getElementById('languageSelect');
        this.typingIndicator = document.getElementById('typingIndicator');
    }
    
    setupEventHandlers() {
        // Language change handler
        if (this.languageSelect) {
            this.languageSelect.addEventListener('change', () => {
                this.currentLanguage = this.languageSelect.value;
                this.updateLanguageTexts();
            });
        }
        
        // Input handlers
        if (this.drugInput) {
            this.drugInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
        
        // Send button handler
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => {
                this.sendMessage();
            });
        }
        
        // Microphone button handler
        if (this.micButton) {
            this.micButton.addEventListener('click', () => {
                this.toggleVoiceInput();
            });
        }
        
        // Keyboard accessibility for mic button
        if (this.micButton) {
            this.micButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleVoiceInput();
                }
            });
        }
    }
    
    setupVoiceRecorder() {
        // Override voice recorder event handlers
        this.voiceRecorder.onRecordingStart = () => {
            this.isProcessing = true;
            this.micButton.classList.add('listening');
            this.showVoiceStatus(this.getLocalizedText('listening'));
            this.micButton.setAttribute('aria-label', 'Stop voice input');
            this.updateInputState(true);
        };
        
        this.voiceRecorder.onRecordingEnd = () => {
            this.isProcessing = false;
            this.micButton.classList.remove('listening');
            this.hideVoiceStatus();
            this.micButton.setAttribute('aria-label', 'Start voice input');
            this.updateInputState(false);
        };
        
        this.voiceRecorder.onTranscriptionComplete = (transcript, confidence) => {
            if (transcript && transcript.trim()) {
                this.drugInput.value = transcript.trim();
                this.drugInput.focus();
                
                // Show confidence indicator if low
                if (confidence < 0.7) {
                    this.showMessage(`Voice input: "${transcript}" (Low confidence - please verify)`, 'warning');
                }
            }
            this.hideVoiceStatus();
        };
        
        this.voiceRecorder.onRecordingError = (error) => {
            this.hideVoiceStatus();
            this.handleVoiceError(error);
        };
    }
    
    // Toggle voice input
    async toggleVoiceInput() {
        if (this.voiceRecorder.isRecording) {
            this.voiceRecorder.stopRecording();
            return;
        }
        
        if (this.isProcessing) {
            return; // Prevent multiple simultaneous recordings
        }
        
        try {
            const speechLangCode = this.voiceRecorder.getSpeechLanguageCode(this.currentLanguage);
            
            // Try Web Speech API first (more reliable)
            if (this.voiceRecorder.recognition) {
                await this.voiceRecorder.startSpeechRecognition(speechLangCode);
            } else {
                // Fallback to MediaRecorder for server processing
                await this.voiceRecorder.startMediaRecording();
            }
            
        } catch (error) {
            this.handleVoiceError(error.message);
        }
    }
    
    // Handle voice input errors
    handleVoiceError(error) {
        let errorMessage = 'Voice input error. ';
        
        if (typeof error === 'string') {
            if (error.includes('not-allowed') || error.includes('permission')) {
                errorMessage = 'Microphone permission denied. Please allow microphone access in your browser settings.';
            } else if (error.includes('no-speech')) {
                errorMessage = 'No speech detected. Please speak clearly and try again.';
            } else if (error.includes('network')) {
                errorMessage = 'Network error. Please check your connection and try again.';
            } else {
                errorMessage += error;
            }
        } else {
            errorMessage += 'Please try typing instead.';
        }
        
        this.showMessage(errorMessage, 'error');
        this.updateInputState(false);
    }
    
    // Update input state (disabled/enabled)
    updateInputState(disabled) {
        if (this.drugInput) {
            this.drugInput.disabled = disabled;
        }
        if (this.sendBtn) {
            this.sendBtn.disabled = disabled;
        }
    }
    
    // Show voice status
    showVoiceStatus(message) {
        if (this.voiceStatus) {
            this.voiceStatus.textContent = message;
            this.voiceStatus.classList.add('show');
        }
    }
    
    // Hide voice status
    hideVoiceStatus() {
        if (this.voiceStatus) {
            this.voiceStatus.classList.remove('show');
        }
    }
    
    // Get localized text
    getLocalizedText(key) {
        const texts = {
            en: {
                listening: 'Listening...',
                processing: 'Processing...',
                translating: 'Translating...',
                placeholder: 'Enter a drug name or click the mic to speak...'
            },
            hi: {
                listening: 'सुन रहा हूं...',
                processing: 'प्रक्रिया कर रहा हूं...',
                translating: 'अनुवाद कर रहा हूं...',
                placeholder: 'दवा का नाम दर्ज करें या बोलने के लिए माइक पर क्लिक करें...'
            },
            ta: {
                listening: 'கேட்கிறேன்...',
                processing: 'செயல்படுத்துகிறேன்...',
                translating: 'மொழிபெயர்க்கிறேன்...',
                placeholder: 'மருந்தின் பெயரை உள்ளிடுங்கள் அல்லது பேச மைக்கை கிளிக் செய்யுங்கள்...'
            }
        };
        
        const langTexts = texts[this.currentLanguage] || texts.en;
        return langTexts[key] || texts.en[key];
    }
    
    // Update language-specific texts
    updateLanguageTexts() {
        const welcomeMsg = document.getElementById('welcomeMessage');
        if (welcomeMsg) {
            // Update welcome message based on language
            const welcomeTexts = {
                en: "Hi! I'm your drug information assistant. Enter any generic drug name and I'll provide you with detailed information. You can type your question or use the microphone button to speak.",
                hi: "नमस्ते! मैं आपका दवा सूचना सहायक हूं। कोई भी जेनेरिक दवा का नाम डालें और मैं आपको विस्तृत जानकारी प्रदान करूंगा।",
                ta: "வணக்கம்! நான் உங்கள் மருந்து தகவல் உதவியாளர். எந்த மருந்தின் பொதுவான பெயரையும் உள்ளிடுங்கள்."
            };
            
            welcomeMsg.textContent = welcomeTexts[this.currentLanguage] || welcomeTexts.en;
        }
        
        if (this.drugInput) {
            this.drugInput.placeholder = this.getLocalizedText('placeholder');
        }
    }
    
    // Enhanced send message with translation
    async sendMessage() {
        const drugName = this.drugInput.value.trim();
        if (!drugName || this.isProcessing) return;
        
        this.addMessage(drugName, 'user');
        this.drugInput.value = '';
        this.updateInputState(true);
        this.showTypingIndicator();
        
        // Show translation status if needed
        if (this.currentLanguage !== 'en') {
            this.showVoiceStatus(this.getLocalizedText('translating'));
        }
        
        try {
            const response = await fetch('/get-drug-info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    drug_name: drugName,
                    language: this.currentLanguage 
                })
            });
            
            const data = await response.json();
            
            this.hideTypingIndicator();
            this.hideVoiceStatus();
            
            if (data.success && data.drug_info) {
                this.addDrugInfoMessage(data.drug_info, data.message);
            } else {
                this.addMessage(data.message || 'Sorry, I could not find information about that drug.', 'bot');
            }
            
        } catch (error) {
            this.hideTypingIndicator();
            this.hideVoiceStatus();
            this.addMessage('Sorry, I encountered an error while searching. Please try again.', 'bot');
            console.error('Error:', error);
        } finally {
            this.updateInputState(false);
            this.drugInput.focus();
        }
    }
    
    // Add message to chat
    addMessage(content, sender, type = 'normal') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        if (type === 'error') {
            messageDiv.classList.add('error-message');
        } else if (type === 'warning') {
            messageDiv.classList.add('warning-message');
        }
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'bot' ? '🤖' : '👤';
        avatar.setAttribute('aria-hidden', 'true');
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        if (sender === 'user') {
            messageDiv.appendChild(messageContent);
            messageDiv.appendChild(avatar);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Auto-remove error/warning messages after 5 seconds
        if (type === 'error' || type === 'warning') {
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, 5000);
        }
    }
    
    // Show message helper
    showMessage(message, type = 'info') {
        this.addMessage(message, 'bot', type);
    }
    
    // Add drug info message (same as original)
    addDrugInfoMessage(drugInfo, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤖';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (message) {
            const messageText = document.createElement('p');
            messageText.textContent = message;
            messageText.style.marginBottom = '15px';
            messageContent.appendChild(messageText);
        }
        
        const drugCard = document.createElement('div');
        drugCard.className = 'drug-info-card';
        
        function getDisplayText(text, maxLength = 500) {
            if (!text || text === 'N/A' || text === 'No information available') {
                return 'Not available';
            }
            if (text.length > maxLength) {
                return text.substring(0, maxLength) + '...';
            }
            return text;
        }
        
        drugCard.innerHTML = `
            <h4>💊 ${drugInfo.generic_name || 'Unknown Drug'}</h4>
            <div class="drug-info-item">
                <span class="drug-info-label">Brand Name:</span>
                <div class="drug-info-value">${getDisplayText(drugInfo.brand_name, 200)}</div>
            </div>
            <div class="drug-info-item">
                <span class="drug-info-label">Manufacturer:</span>
                <div class="drug-info-value">${getDisplayText(drugInfo.manufacturer, 200)}</div>
            </div>
            <div class="drug-info-item">
                <span class="drug-info-label">What it's used for:</span>
                <div class="drug-info-value">${getDisplayText(drugInfo.indications, 400)}</div>
            </div>
            <div class="drug-info-item">
                <span class="drug-info-label">Dosage Information:</span>
                <div class="drug-info-value">${getDisplayText(drugInfo.dosage, 400)}</div>
            </div>
            <div class="drug-info-item">
                <span class="drug-info-label">Warnings:</span>
                <div class="drug-info-value">${getDisplayText(drugInfo.warnings, 300)}</div>
            </div>
            <div class="drug-info-item">
                <span class="drug-info-label">Side Effects:</span>
                <div class="drug-info-value">${getDisplayText(drugInfo.side_effects, 300)}</div>
            </div>
        `;
        
        messageContent.appendChild(drugCard);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    // Show typing indicator
    showTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'flex';
            this.scrollToBottom();
        }
    }
    
    // Hide typing indicator
    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }
    
    // Scroll to bottom
    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }
}

// Initialize the chatbot when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatbotUI = new ChatbotUIController();
    
    // Check browser compatibility
    if (!window.fetch) {
        console.error('Browser not supported');
        document.body.innerHTML += '<div class="error-message">Your browser is not supported. Please update your browser.</div>';
    }
    
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && window.chatbotUI && window.chatbotUI.voiceRecorder.isRecording) {
            window.chatbotUI.voiceRecorder.stopRecording();
        }
    });
});

// Legacy function support (for existing onclick handlers)
function toggleVoiceInput() {
    if (window.chatbotUI) {
        window.chatbotUI.toggleVoiceInput();
    }
}

function sendMessage() {
    if (window.chatbotUI) {
        window.chatbotUI.sendMessage();
    }
}

function changeLanguage() {
    if (window.chatbotUI) {
        window.chatbotUI.currentLanguage = document.getElementById('languageSelect').value;
        window.chatbotUI.updateLanguageTexts();
    }
}