/**
 * Artin Smart Realty - Live Chat Monitor (Eagle Eye Mode)
 * Watch bot conversations in real-time and take control when needed
 * Features: Human Takeover, Whisper Mode (internal notes)
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Hand,
  Bot,
  Send,
  Eye,
  MessageSquare,
  User,
  AlertTriangle,
  MoreVertical,
  Phone,
  X,
  Clock,
  RefreshCw,
  Mic,
  Image as ImageIcon,
  Paperclip,
  Lock,
  Unlock,
} from 'lucide-react';
import io from 'socket.io-client';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Chat message component
const ChatMessage = ({ message, isWhisper = false }) => {
  const isUser = message.direction === 'inbound' || message.sender === 'user';
  const isBot = message.sender === 'bot' || message.ai_generated;
  const isAgent = message.sender === 'agent';

  const getMessageStyle = () => {
    if (isWhisper) return 'chat-message-whisper';
    if (isUser) return 'chat-message-user';
    return 'chat-message-bot';
  };

  const getSenderLabel = () => {
    if (isWhisper) return '🔒 Internal Note';
    if (isUser) return 'Customer';
    if (isBot) return '🤖 Bot';
    if (isAgent) return '👤 Agent';
    return 'System';
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : isWhisper ? 'justify-center' : 'justify-start'}`}>
      <div className={`${getMessageStyle()} max-w-[75%]`}>
        <div className={`text-xs mb-1 ${isWhisper ? 'text-purple-400' : 'text-gray-400'}`}>
          {getSenderLabel()}
        </div>
        <p className="text-sm">{message.text || message.message_text}</p>
        <div className={`text-xs mt-1 ${isWhisper ? 'text-purple-400/60' : 'text-gray-500'}`}>
          {message.timestamp || new Date(message.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

// Active chat card component
const ActiveChatCard = ({ chat, isSelected, onClick }) => {
  const getStatusBadge = () => {
    if (chat.is_taken_over) {
      return <span className="badge badge-green text-xs">Agent Active</span>;
    }
    return <span className="badge badge-blue text-xs">Bot Handling</span>;
  };

  return (
    <div
      onClick={onClick}
      className={`p-4 cursor-pointer transition-all border-l-4 ${isSelected
        ? 'bg-gold-500/10 border-l-gold-500'
        : 'bg-navy-800/30 border-l-transparent hover:bg-navy-700/50'
        }`}
    >
      <div className="flex items-start gap-3">
        <div className="lead-avatar flex-shrink-0 w-10 h-10">
          {chat.name?.charAt(0)?.toUpperCase() || '?'}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-white truncate">{chat.name || `Lead #${chat.id}`}</h4>
            {getStatusBadge()}
          </div>
          <p className="text-sm text-gray-400 truncate mt-1">
            {chat.last_message || 'No messages yet'}
          </p>
          <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {chat.last_message_at ? new Date(chat.last_message_at).toLocaleTimeString() : 'Just now'}
          </p>
        </div>
      </div>
    </div>
  );
};

// Main Live Chat Monitor component
export default function LiveChatMonitor({ tenantId, token }) {
  const [activeChats, setActiveChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isWhisperMode, setIsWhisperMode] = useState(false);
  const [isTakenOver, setIsTakenOver] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  const messagesEndRef = useRef(null);
  const socketRef = useRef(null);

  // Connect to WebSocket for real-time updates
  useEffect(() => {
    loadActiveChats();
    // Only connect WebSocket if API_BASE_URL is available
    if (API_BASE_URL) {
      connectWebSocket();
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, token]);

  const connectWebSocket = useCallback(() => {
    try {
      // Check if socket.io is available
      if (typeof io === 'undefined') {
        console.warn('Socket.io not available, real-time updates disabled');
        return;
      }

      const wsUrl = API_BASE_URL.replace('http', 'ws') || 'ws://localhost:8000';
      socketRef.current = io(wsUrl, {
        auth: { token },
        query: { tenant_id: tenantId },
        reconnectionAttempts: 3,
        timeout: 5000,
      });

      socketRef.current.on('connect_error', (error) => {
        console.warn('WebSocket connection error:', error.message);
      });

      socketRef.current.on('new_message', (data) => {
        if (selectedChat && data.lead_id === selectedChat.id) {
          setMessages(prev => [...prev, data]);
          scrollToBottom();
        }

        // Update last message in chat list
        setActiveChats(prev => prev.map(chat =>
          chat.id === data.lead_id
            ? { ...chat, last_message: data.text, last_message_at: new Date().toISOString() }
            : chat
        ));
      });

      socketRef.current.on('new_lead', (data) => {
        // Play notification sound
        if (window.showNotification) {
          window.showNotification({
            type: 'new_lead',
            title: '🔔 New Chat!',
            message: `${data.name || 'New lead'} started a conversation`,
          });
        }
        loadActiveChats();
      });

      socketRef.current.on('takeover_status', (data) => {
        if (selectedChat && data.lead_id === selectedChat.id) {
          setIsTakenOver(data.is_taken_over);
        }
      });

    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  }, [tenantId, token, selectedChat]);

  const loadActiveChats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/chats/active`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setActiveChats(Array.isArray(data) ? data : (data.chats || []));
      }
    } catch (error) {
      console.error('Error loading active chats:', error);
      // Sample data for demo
      setActiveChats([
        { id: 1, name: 'Sarah Jenkins', last_message: 'I am interested in the Palm Jumeirah villa', last_message_at: new Date().toISOString(), is_taken_over: false },
        { id: 2, name: 'Michael Chen', last_message: 'What is the price for the downtown penthouse?', last_message_at: new Date(Date.now() - 300000).toISOString(), is_taken_over: true },
        { id: 3, name: 'Emma Davis', last_message: 'Can I schedule a viewing?', last_message_at: new Date(Date.now() - 600000).toISOString(), is_taken_over: false },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadChatHistory = async (leadId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chats/${leadId}/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMessages(Array.isArray(data) ? data : (data.messages || []));
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      // Sample messages for demo
      setMessages([
        { id: 1, text: 'Hello! I am looking for a luxury villa in Palm Jumeirah.', sender: 'user', created_at: new Date(Date.now() - 600000) },
        { id: 2, text: 'Welcome! I\'d be happy to help you find your perfect property. What is your budget range?', sender: 'bot', ai_generated: true, created_at: new Date(Date.now() - 550000) },
        { id: 3, text: 'Around $3-5 million, preferably with a pool and garden.', sender: 'user', created_at: new Date(Date.now() - 500000) },
        { id: 4, text: 'Excellent! We have several stunning villas in that range. Would you prefer a beachfront or garden view?', sender: 'bot', ai_generated: true, created_at: new Date(Date.now() - 450000) },
      ]);
    }
    scrollToBottom();
  };

  const handleSelectChat = (chat) => {
    setSelectedChat(chat);
    setIsTakenOver(chat.is_taken_over);
    loadChatHistory(chat.id);
  };

  // Handle Human Takeover - "I'll Handle This" button
  const handleTakeover = async () => {
    if (!selectedChat) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chats/${selectedChat.id}/takeover`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        setIsTakenOver(true);
        setActiveChats(prev => prev.map(chat =>
          chat.id === selectedChat.id ? { ...chat, is_taken_over: true } : chat
        ));

        // Add system message
        setMessages(prev => [...prev, {
          id: Date.now(),
          text: '🖐️ Agent has taken over this conversation',
          sender: 'system',
          created_at: new Date()
        }]);
      }
    } catch (error) {
      console.error('Error taking over chat:', error);
      // Optimistically update for demo
      setIsTakenOver(true);
    }
  };

  // Release chat back to bot
  const handleRelease = async () => {
    if (!selectedChat) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chats/${selectedChat.id}/release`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        setIsTakenOver(false);
        setActiveChats(prev => prev.map(chat =>
          chat.id === selectedChat.id ? { ...chat, is_taken_over: false } : chat
        ));

        // Add system message
        setMessages(prev => [...prev, {
          id: Date.now(),
          text: '🤖 Bot has resumed handling this conversation',
          sender: 'system',
          created_at: new Date()
        }]);
      }
    } catch (error) {
      console.error('Error releasing chat:', error);
      setIsTakenOver(false);
    }
  };

  // Send message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedChat) return;

    setSending(true);
    const messageText = newMessage;
    setNewMessage('');

    try {
      if (isWhisperMode) {
        // Send as internal whisper note (not visible to customer)
        await fetch(`${API_BASE_URL}/api/v1/chats/${selectedChat.id}/whisper`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ message: messageText })
        });

        // Add whisper message locally
        setMessages(prev => [...prev, {
          id: Date.now(),
          text: messageText,
          sender: 'whisper',
          isWhisper: true,
          created_at: new Date()
        }]);
      } else {
        // Send as regular message
        await fetch(`${API_BASE_URL}/api/v1/chats/${selectedChat.id}/send`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ message: messageText })
        });

        // Add message locally
        setMessages(prev => [...prev, {
          id: Date.now(),
          text: messageText,
          sender: 'agent',
          created_at: new Date()
        }]);
      }

      scrollToBottom();
    } catch (error) {
      console.error('Error sending message:', error);
      // Add message locally for demo
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: messageText,
        sender: isWhisperMode ? 'whisper' : 'agent',
        isWhisper: isWhisperMode,
        created_at: new Date()
      }]);
    } finally {
      setSending(false);
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-200px)] flex glass-card overflow-hidden">
      {/* Chat List Sidebar */}
      <div className="w-80 border-r border-white/5 flex flex-col">
        <div className="p-4 border-b border-white/5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Eye className="w-5 h-5 text-gold-400" />
              Live Chats
            </h3>
            <button
              onClick={loadActiveChats}
              className="p-2 rounded-lg hover:bg-navy-700 text-gray-400 hover:text-white transition-all"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">{activeChats.length} active conversations</p>
        </div>

        <div className="flex-1 overflow-y-auto">
          {activeChats.map((chat) => (
            <ActiveChatCard
              key={chat.id}
              chat={chat}
              isSelected={selectedChat?.id === chat.id}
              onClick={() => handleSelectChat(chat)}
            />
          ))}

          {activeChats.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No active chats
            </div>
          )}
        </div>
      </div>

      {/* Chat Window */}
      <div className="flex-1 flex flex-col">
        {selectedChat ? (
          <>
            {/* Chat Header */}
            <div className="chat-header">
              <div className="flex items-center gap-3">
                <div className="lead-avatar">
                  {selectedChat.name?.charAt(0)?.toUpperCase() || '?'}
                </div>
                <div>
                  <h4 className="font-semibold text-white">{selectedChat.name || 'Unknown'}</h4>
                  <p className="text-xs text-gray-400">
                    {isTakenOver ? '👤 You are handling this chat' : '🤖 Bot is responding'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {!isTakenOver ? (
                  <button
                    onClick={handleTakeover}
                    className="takeover-btn"
                    title="Take over this chat"
                  >
                    <Hand className="w-4 h-4" />
                    <span>I'll Handle This</span>
                  </button>
                ) : (
                  <button
                    onClick={handleRelease}
                    className="takeover-btn takeover-active"
                    title="Release to bot"
                  >
                    <Bot className="w-4 h-4" />
                    <span>Release to Bot</span>
                  </button>
                )}
              </div>
            </div>

            {/* Messages */}
            <div className="chat-messages">
              {messages.map((msg, index) => (
                <ChatMessage
                  key={msg.id || index}
                  message={msg}
                  isWhisper={msg.isWhisper || msg.sender === 'whisper'}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="chat-input-container">
              {/* Whisper Mode Toggle */}
              <div className="flex items-center justify-between mb-3">
                <button
                  onClick={() => setIsWhisperMode(!isWhisperMode)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all ${isWhisperMode
                    ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                    : 'text-gray-400 hover:text-white hover:bg-navy-700'
                    }`}
                >
                  {isWhisperMode ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                  <span>{isWhisperMode ? 'Whisper Mode ON' : 'Whisper Mode'}</span>
                </button>

                {isWhisperMode && (
                  <span className="text-xs text-purple-400">
                    🔒 Message will be internal only (not sent to customer)
                  </span>
                )}
              </div>

              <form onSubmit={handleSendMessage} className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder={isWhisperMode ? "Add internal note for team..." : "Type a message..."}
                    className={`input-field pr-20 ${isWhisperMode ? 'border-purple-500/30 bg-purple-500/5' : ''}`}
                    disabled={!isTakenOver && !isWhisperMode}
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    <button type="button" className="p-2 text-gray-400 hover:text-white">
                      <Paperclip className="w-4 h-4" />
                    </button>
                    <button type="button" className="p-2 text-gray-400 hover:text-white">
                      <ImageIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={!newMessage.trim() || sending || (!isTakenOver && !isWhisperMode)}
                  className={`btn-gold flex items-center gap-2 ${(!newMessage.trim() || sending || (!isTakenOver && !isWhisperMode))
                    ? 'opacity-50 cursor-not-allowed'
                    : ''
                    }`}
                >
                  <Send className="w-4 h-4" />
                  <span>{sending ? 'Sending...' : 'Send'}</span>
                </button>
              </form>

              {!isTakenOver && !isWhisperMode && (
                <p className="text-xs text-yellow-400 mt-2 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Take over the chat to send messages to customer
                </p>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
            <Eye className="w-16 h-16 mb-4 text-gray-600" />
            <h3 className="text-lg font-medium text-white">Eagle Eye Mode</h3>
            <p className="text-sm mt-2">Select a chat to monitor the conversation</p>
          </div>
        )}
      </div>
    </div>
  );
}
