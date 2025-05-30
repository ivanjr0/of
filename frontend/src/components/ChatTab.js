import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageCircle, Plus, Trash2, Clock, User, Bot } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';
import DebugToolbar from './DebugToolbar';
import { getAuthHeader } from '../utils/auth';

function ChatTab({ sessions, setSessions }) {
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [debugInfo, setDebugInfo] = useState(null);
  const messagesEndRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (currentSession) {
      loadMessages();
    }
  }, [currentSession]);

  // Cleanup polling on unmount or session change
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [currentSession]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSessions = async () => {
    try {
      const response = await axios.get('/api/sessions', {
        headers: getAuthHeader()
      });
      // Ensure sessions is always an array
      const sessionsData = Array.isArray(response.data) ? response.data : [];
      setSessions(sessionsData);
      
      if (sessionsData.length > 0 && !currentSession) {
        setCurrentSession(sessionsData[0]);
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
      // Set empty array on error
      setSessions([]);
      
      if (error.response?.status === 401) {
        toast.error('Please log in to access chat sessions');
      } else if (error.response?.status !== 404) {
        toast.error('Failed to load chat sessions');
      }
    }
  };

  const loadMessages = async () => {
    if (!currentSession) return;
    
    setIsLoading(true);
    try {
      const response = await axios.get(`/api/sessions/${currentSession.id}/messages`, {
        headers: getAuthHeader()
      });
      setMessages(response.data.messages || response.data);
      
      // If response includes debug info, set it
      if (response.data.debug_info) {
        setDebugInfo(response.data.debug_info);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
      if (error.response?.status === 401) {
        toast.error('Please log in to access messages');
      } else {
        toast.error('Failed to load conversation history');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await axios.post('/api/sessions', {
        title: `Chat Session ${new Date().toLocaleString()}`
      }, {
        headers: getAuthHeader()
      });
      
      const newSession = response.data;
      setSessions(prev => [newSession, ...(Array.isArray(prev) ? prev : [])]);
      setCurrentSession(newSession);
      setMessages([]);
      toast.success('New chat session created!');
    } catch (error) {
      console.error('Error creating session:', error);
      if (error.response?.status === 401) {
        toast.error('Please log in to create a chat session');
      } else {
        toast.error('Failed to create new chat session');
      }
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      await axios.delete(`/api/sessions/${sessionId}`, {
        headers: getAuthHeader()
      });
      setSessions(prev => Array.isArray(prev) ? prev.filter(s => s.id !== sessionId) : []);
      
      if (currentSession?.id === sessionId) {
        const remainingSessions = Array.isArray(sessions) ? sessions.filter(s => s.id !== sessionId) : [];
        setCurrentSession(remainingSessions.length > 0 ? remainingSessions[0] : null);
        setMessages([]);
      }
      
      toast.success('Chat session deleted');
    } catch (error) {
      console.error('Error deleting session:', error);
      if (error.response?.status === 401) {
        toast.error('Please log in to delete sessions');
      } else {
        toast.error('Failed to delete chat session');
      }
    }
  };

  const startPolling = () => {
    setIsPolling(true);
    
    // Poll every 1 second for new messages
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await axios.get(`/api/sessions/${currentSession.id}/messages`, {
          headers: getAuthHeader()
        });
        const newMessages = response.data.messages || response.data;
        
        // Check if we received a new assistant message
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant') {
          // Assistant has responded, stop polling
          setMessages(newMessages);
          
          // Update debug info if available
          if (response.data.debug_info) {
            setDebugInfo(response.data.debug_info);
          }
          
          stopPolling();
          toast.success('AI has responded!');
        } else {
          // Update messages but keep polling
          setMessages(newMessages);
        }
      } catch (error) {
        console.error('Error during polling:', error);
        // Don't stop polling on error, the assistant might still be processing
      }
    }, 1000);
  };

  const stopPolling = () => {
    setIsPolling(false);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const sendMessage = async () => {
    if (!messageInput.trim() || !currentSession || isSending) return;

    const userMessage = messageInput.trim();
    setMessageInput('');
    setIsSending(true);

    // Add user message to UI immediately
    const tempUserMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
      id: Date.now()
    };
    setMessages(prev => [...prev, tempUserMessage]);

    try {
      const response = await axios.post(`/api/sessions/${currentSession.id}/messages`, {
        content: userMessage
      }, {
        headers: getAuthHeader()
      });

      // Start polling for the assistant's response
      startPolling();
      
      toast.success('Message sent! AI is thinking...');
    } catch (error) {
      console.error('Error sending message:', error);
      if (error.response?.status === 401) {
        toast.error('Please log in to send messages');
      } else {
        toast.error('Failed to send message');
      }
      // Remove the temporary message on error
      setMessages(prev => prev.filter(msg => msg.id !== tempUserMessage.id));
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="card chat-tab">
      <div className="chat-header">
        <div className="chat-title">
          <MessageCircle size={24} />
          <h2>AI Learning Assistant</h2>
          <p>Ask questions about your educational content</p>
        </div>
        <button onClick={createNewSession} className="btn btn-primary">
          <Plus size={20} />
          New Chat
        </button>
      </div>

      <div className="chat-container">
        {/* Sessions sidebar */}
        <div className="sessions-sidebar">
          <h3>Chat Sessions</h3>
          <div className="sessions-list">
            {(Array.isArray(sessions) ? sessions : []).map(session => (
              <div
                key={session.id}
                className={`session-item ${currentSession?.id === session.id ? 'active' : ''}`}
                onClick={() => setCurrentSession(session)}
              >
                <div className="session-info">
                  <span className="session-title">{session.title}</span>
                  <span className="session-meta">
                    <Clock size={14} />
                    {formatTime(session.updated_at)}
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  className="session-delete"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
            {(!sessions || sessions.length === 0) && (
              <div className="empty-sessions">
                <p>No chat sessions yet</p>
                <button onClick={createNewSession} className="btn btn-secondary">
                  Start your first chat
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Chat area */}
        <div className="chat-area">
          {currentSession ? (
            <>
              <div className="messages-container">
                {isLoading ? (
                  <div className="loading-messages">
                    <LoadingSpinner />
                    <span>Loading conversation...</span>
                  </div>
                ) : (
                  <>
                    {messages.map((message, index) => (
                      <div
                        key={message.id || index}
                        className={`message ${message.role}`}
                      >
                        <div className="message-avatar">
                          {message.role === 'user' ? (
                            <User size={20} />
                          ) : (
                            <Bot size={20} />
                          )}
                        </div>
                        <div className="message-content">
                          <div className="message-text">{message.content}</div>
                          <div className="message-time">
                            {formatTime(message.timestamp)}
                          </div>
                        </div>
                      </div>
                    ))}
                    {isPolling && (
                      <div className="message assistant typing">
                        <div className="message-avatar">
                          <Bot size={20} />
                        </div>
                        <div className="message-content">
                          <div className="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              <div className="message-input-container">
                <div className="message-input-wrapper">
                  <textarea
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about your educational content..."
                    disabled={isSending}
                    rows="1"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!messageInput.trim() || isSending}
                    className="btn btn-primary send-btn"
                  >
                    {isSending ? (
                      <LoadingSpinner size="small" />
                    ) : (
                      <Send size={20} />
                    )}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="no-session">
              <MessageCircle size={64} />
              <h3>No chat session selected</h3>
              <p>Create a new chat session to start talking with your AI assistant</p>
              <button onClick={createNewSession} className="btn btn-primary btn-large">
                <Plus size={20} />
                Start New Chat
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Debug Toolbar */}
      <DebugToolbar debugInfo={debugInfo} />
    </div>
  );
}

export default ChatTab; 