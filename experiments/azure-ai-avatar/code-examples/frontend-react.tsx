/**
 * React Frontend for AI Avatar
 *
 * Features:
 * - Real-time conversation via SignalR
 * - Speech recognition and synthesis
 * - Avatar rendering with lip-sync
 * - Message history display
 */

import React, { useState, useEffect, useRef } from 'react';
import * as signalR from '@microsoft/signalr';

// ============================================
// TYPES
// ============================================

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface VisemeData {
  visemeId: number;
  audioOffset: number;
}

interface ConversationResponse {
  responseText: string;
  visemes: VisemeData[];
  audioUrl: string;
  metadata: Record<string, any>;
}

// ============================================
// AVATAR COMPONENT
// ============================================

export const AvatarChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const hubConnectionRef = useRef<signalR.HubConnection | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const audioRef = useRef<HTMLAudioElement>(new Audio());

  // ============================================
  // INITIALIZATION
  // ============================================

  useEffect(() => {
    initializeSession();
    initializeSpeechRecognition();
    initializeSignalR();

    return () => {
      cleanup();
    };
  }, []);

  async function initializeSession() {
    try {
      const response = await fetch(`${API_URL}/api/avatar/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: getUserId() })
      });

      const data = await response.json();
      setSessionId(data.sessionId);
      console.log('✅ Session created:', data.sessionId);
    } catch (error) {
      console.error('❌ Failed to create session:', error);
    }
  }

  function initializeSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window)) {
      console.warn('Speech recognition not supported');
      return;
    }

    const SpeechRecognition = window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
      console.log('🎤 Listening...');
    };

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');

      if (event.results[0].isFinal) {
        setInputText(transcript);
        sendMessage(transcript);
      }
    };

    recognition.onerror = (event) => {
      console.error('❌ Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      console.log('🛑 Stopped listening');
    };

    recognitionRef.current = recognition;
  }

  async function initializeSignalR() {
    const connection = new signalR.HubConnectionBuilder()
      .withUrl(`${API_URL}/hub/avatar`)
      .withAutomaticReconnect()
      .configureLogging(signalR.LogLevel.Information)
      .build();

    // Handle avatar responses
    connection.on('AvatarResponse', handleAvatarResponse);

    // Handle status updates
    connection.on('AvatarStatus', (status) => {
      console.log('📊 Avatar status:', status);
      if (status.status === 'thinking') {
        setIsThinking(true);
      }
    });

    // Handle reconnection
    connection.onreconnecting(() => {
      console.log('🔄 Reconnecting to SignalR...');
    });

    connection.onreconnected(() => {
      console.log('✅ Reconnected to SignalR');
      if (sessionId) {
        connection.invoke('JoinSession', sessionId);
      }
    });

    try {
      await connection.start();
      console.log('✅ SignalR connected');
      hubConnectionRef.current = connection;
    } catch (error) {
      console.error('❌ SignalR connection failed:', error);
    }
  }

  // ============================================
  // MESSAGING
  // ============================================

  async function sendMessage(text: string) {
    if (!text.trim() || !sessionId) return;

    // Add user message to UI
    const userMessage: Message = {
      role: 'user',
      content: text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Clear input
    setInputText('');
    setIsThinking(true);

    try {
      // Send to API
      const response = await fetch(
        `${API_URL}/api/avatar/conversation/${sessionId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            userId: getUserId(),
            message: text,
            language: 'en-US'
          })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      // Response will come via SignalR
    } catch (error) {
      console.error('❌ Error sending message:', error);
      setIsThinking(false);

      // Show error message
      const errorMessage: Message = {
        role: 'assistant',
        content: "I'm sorry, I'm having trouble responding right now.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }

  function handleAvatarResponse(response: ConversationResponse) {
    console.log('📥 Avatar response:', response);

    setIsThinking(false);

    // Add assistant message to UI
    const assistantMessage: Message = {
      role: 'assistant',
      content: response.responseText,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, assistantMessage]);

    // Play audio with visemes
    playAudioWithVisemes(response.audioUrl, response.visemes);
  }

  // ============================================
  // AUDIO & AVATAR ANIMATION
  // ============================================

  async function playAudioWithVisemes(
    audioUrl: string,
    visemes: VisemeData[]
  ) {
    setIsSpeaking(true);

    const audio = audioRef.current;
    audio.src = audioUrl;

    // Schedule viseme animations
    const startTime = Date.now();
    audio.addEventListener('play', () => {
      visemes.forEach((viseme) => {
        setTimeout(() => {
          animateAvatarMouth(viseme.visemeId);
        }, viseme.audioOffset / 10000); // Convert to ms
      });
    });

    audio.addEventListener('ended', () => {
      setIsSpeaking(false);
      resetAvatarMouth();
    });

    try {
      await audio.play();
    } catch (error) {
      console.error('❌ Audio playback failed:', error);
      setIsSpeaking(false);
    }
  }

  function animateAvatarMouth(visemeId: number) {
    // Map viseme ID to avatar animation
    // This is a placeholder - implement based on your avatar library
    const mouthShape = VISEME_MAP[visemeId] || 'neutral';
    console.log(`👄 Mouth shape: ${mouthShape}`);

    // Example: Update avatar state
    // avatarRenderer.setMouthShape(mouthShape);
  }

  function resetAvatarMouth() {
    // Return to neutral expression
    // avatarRenderer.setMouthShape('neutral');
  }

  // ============================================
  // USER INTERACTIONS
  // ============================================

  function handleStartVoiceInput() {
    if (recognitionRef.current) {
      recognitionRef.current.start();
    }
  }

  function handleStopVoiceInput() {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendMessage(inputText);
  }

  // ============================================
  // CLEANUP
  // ============================================

  function cleanup() {
    if (hubConnectionRef.current) {
      hubConnectionRef.current.stop();
    }
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    audioRef.current.pause();
  }

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="avatar-chat-container">
      {/* Avatar Display */}
      <div className="avatar-display">
        <div className="avatar-canvas" id="avatar-canvas">
          {/* Avatar renderer goes here */}
          <AvatarRenderer
            isListening={isListening}
            isThinking={isThinking}
            isSpeaking={isSpeaking}
          />
        </div>

        {/* Status Indicator */}
        <div className="status-indicator">
          {isListening && <span className="status listening">🎤 Listening...</span>}
          {isThinking && <span className="status thinking">💭 Thinking...</span>}
          {isSpeaking && <span className="status speaking">💬 Speaking...</span>}
        </div>
      </div>

      {/* Chat History */}
      <div className="chat-history">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${msg.role}`}
          >
            <div className="message-content">
              <strong>{msg.role === 'user' ? 'You' : 'Avatar'}:</strong>
              <p>{msg.content}</p>
            </div>
            <div className="message-timestamp">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        <div ref={(el) => el?.scrollIntoView({ behavior: 'smooth' })} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="input-area">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Type a message or click the microphone..."
          disabled={isThinking || isSpeaking}
          className="message-input"
        />

        <button
          type="button"
          onClick={isListening ? handleStopVoiceInput : handleStartVoiceInput}
          disabled={isThinking || isSpeaking}
          className={`voice-button ${isListening ? 'active' : ''}`}
          aria-label={isListening ? 'Stop listening' : 'Start voice input'}
        >
          🎤
        </button>

        <button
          type="submit"
          disabled={!inputText.trim() || isThinking || isSpeaking}
          className="send-button"
        >
          Send
        </button>
      </form>
    </div>
  );
};

// ============================================
// AVATAR RENDERER COMPONENT
// ============================================

interface AvatarRendererProps {
  isListening: boolean;
  isThinking: boolean;
  isSpeaking: boolean;
}

const AvatarRenderer: React.FC<AvatarRendererProps> = ({
  isListening,
  isThinking,
  isSpeaking
}) => {
  return (
    <div className="avatar">
      {/* Placeholder - integrate with actual avatar library */}
      <div className="avatar-placeholder">
        <div className={`avatar-state ${getAvatarState()}`}>
          <img
            src="/avatar-image.png"
            alt="AI Avatar"
            className="avatar-image"
          />
        </div>
      </div>
    </div>
  );

  function getAvatarState() {
    if (isSpeaking) return 'speaking';
    if (isThinking) return 'thinking';
    if (isListening) return 'listening';
    return 'idle';
  }
};

// ============================================
// UTILITIES
// ============================================

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function getUserId(): string {
  // Get or create user ID
  let userId = localStorage.getItem('userId');
  if (!userId) {
    userId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('userId', userId);
  }
  return userId;
}

const VISEME_MAP: Record<number, string> = {
  0: 'sil',
  1: 'ae',
  2: 'aa',
  3: 'ao',
  4: 'ey',
  5: 'eh',
  6: 'ih',
  7: 'iy',
  8: 'uh',
  9: 'uw',
  10: 'ah',
  11: 'er',
  12: 'r',
  13: 'l',
  14: 's',
  15: 'sh',
  16: 'z',
  17: 'ch',
  18: 'f',
  19: 'th',
  20: 'p',
  21: 'k',
};

// ============================================
// STYLES (CSS-in-JS or separate file)
// ============================================

const styles = `
.avatar-chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.avatar-display {
  flex: 0 0 400px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.avatar-canvas {
  width: 300px;
  height: 300px;
  border-radius: 50%;
  overflow: hidden;
  background: white;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.status-indicator {
  position: absolute;
  bottom: 20px;
  background: rgba(255,255,255,0.9);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status.listening { color: #10b981; }
.status.thinking { color: #f59e0b; }
.status.speaking { color: #3b82f6; }

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f9fafb;
}

.message {
  margin-bottom: 16px;
  animation: slideIn 0.3s ease-out;
}

.message.user .message-content {
  background: #3b82f6;
  color: white;
  margin-left: auto;
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px 18px 4px 18px;
}

.message.assistant .message-content {
  background: white;
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px 18px 18px 4px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 16px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 24px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
}

.message-input:focus {
  border-color: #3b82f6;
}

.voice-button {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: #f3f4f6;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.voice-button:hover {
  background: #e5e7eb;
}

.voice-button.active {
  background: #ef4444;
  animation: pulse 1.5s infinite;
}

.send-button {
  padding: 12px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 24px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.send-button:hover:not(:disabled) {
  background: #2563eb;
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
`;

export default AvatarChat;
