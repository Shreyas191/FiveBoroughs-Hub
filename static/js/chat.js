const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const voiceButton = document.getElementById('voiceButton');
const voiceStatus = document.getElementById('voiceStatus');
const browserWarning = document.getElementById('browserWarning');

// Speech Recognition setup
let recognition = null;
let isListening = false;

// Check for browser support
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;  // Stop after user finishes speaking
    recognition.interimResults = true;  // Show real-time results
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;
    
    // Handle speech recognition results
    recognition.onresult = (event) => {
        let transcript = '';
        let isFinal = false;
        
        // Get the transcript
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript = event.results[i][0].transcript;
            isFinal = event.results[i].isFinal;
        }
        
        // Update input field with transcript
        userInput.value = transcript;
        
        // If speech is final, automatically send the message
        if (isFinal) {
            console.log('Final transcript:', transcript);
            stopListening();
            // Small delay to show the final transcript before sending
            setTimeout(() => {
                sendMessage();
            }, 500);
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopListening();
        
        let errorMessage = 'Voice input error. ';
        switch(event.error) {
            case 'no-speech':
                errorMessage += 'No speech detected. Please try again.';
                break;
            case 'audio-capture':
                errorMessage += 'Microphone not found or not allowed.';
                break;
            case 'not-allowed':
                errorMessage += 'Microphone permission denied.';
                break;
            default:
                errorMessage += 'Please try again.';
        }
        
        addSystemMessage(errorMessage);
    };
    
    recognition.onend = () => {
        console.log('Speech recognition ended');
        stopListening();
    };
    
} else {
    // Browser doesn't support speech recognition
    voiceButton.style.display = 'none';
    browserWarning.classList.remove('hidden');
    console.warn('Speech recognition not supported in this browser');
}

// Voice button click handler
voiceButton.addEventListener('click', () => {
    if (isListening) {
        stopListening();
    } else {
        startListening();
    }
});

function startListening() {
    if (!recognition) return;
    
    try {
        recognition.start();
        isListening = true;
        voiceButton.classList.add('listening');
        voiceStatus.classList.remove('hidden');
        userInput.placeholder = 'Listening... Speak now!';
        console.log('Started listening...');
    } catch (error) {
        console.error('Error starting speech recognition:', error);
        addSystemMessage('Could not start voice input. Please check microphone permissions.');
    }
}

function stopListening() {
    if (!recognition) return;
    
    try {
        recognition.stop();
    } catch (error) {
        console.error('Error stopping recognition:', error);
    }
    
    isListening = false;
    voiceButton.classList.remove('listening');
    voiceStatus.classList.add('hidden');
    userInput.placeholder = 'Ask about NYC transit or click 🎤 to speak...';
    console.log('Stopped listening');
}

// Send message on button click
sendButton.addEventListener('click', sendMessage);

// Send message on Enter key
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;
    
    // Display user message
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    
    // Disable input while processing
    userInput.disabled = true;
    sendButton.disabled = true;
    voiceButton.disabled = true;
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    try {
        // Send request to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        typingIndicator.remove();
        
        if (response.ok) {
            // Display bot response
            addMessage(data.response, 'bot');
            
            // Optional: Speak the response (text-to-speech)
            // speakResponse(data.response);
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        typingIndicator.remove();
        addMessage('Sorry, I couldn\'t connect to the server. Please check your connection.', 'bot');
        console.error('Error:', error);
    } finally {
        // Re-enable input
        userInput.disabled = false;
        sendButton.disabled = false;
        voiceButton.disabled = false;
        userInput.focus();
    }
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMessage(text);
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.style.background = '#f39c12';
    contentDiv.style.color = 'white';
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
    
    return messageDiv;
}

function addTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'typing-indicator';
    indicatorDiv.innerHTML = '<span></span><span></span><span></span>';
    
    messageDiv.appendChild(indicatorDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function formatMessage(text) {
    // Convert line breaks to <br>
    text = text.replace(/\n/g, '<br>');
    
    // Convert markdown-style bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert markdown-style lists
    text = text.replace(/^- (.*?)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    return text;
}

// Optional: Text-to-Speech for bot responses
function speakResponse(text) {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Speak
        window.speechSynthesis.speak(utterance);
    }
}

// Focus input on load
userInput.focus();

// Stop listening if user clicks outside voice button while recording
document.addEventListener('click', (e) => {
    if (isListening && !voiceButton.contains(e.target)) {
        // Don't stop immediately - let user speak
        // stopListening();
    }
});
