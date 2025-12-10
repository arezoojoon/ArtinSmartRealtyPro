import { useState, useEffect, useRef } from 'react';
import { getActiveChats, getChatHistory, takeoverChat, releaseChat, sendManualMessage } from '../../api/client';
import { Hand, Bot, Send, Eye, MessageSquare } from 'lucide-react';
import io from 'socket.io-client';

/**
 * Live Chat Takeover - Eagle Eye Mode
 * Watch bot conversations in real-time and take control when needed
 */

export default function LiveChatMonitor() {
  const [activeChats, setActiveChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isTakenOver, setIsTakenOver] = useState(false);
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  
  useEffect(() => {
    loadActiveChats();
    connectWebSocket();
    
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);
  
  useEffect(() => {
    if (selectedChat) {
      loadChatHistory(selectedChat.lead_id);
    }
  }, [selectedChat]);
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const connectWebSocket = () => {
    const socket = io(import.meta.env.VITE_WS_URL || 'ws://localhost:8000', {
      transports: ['websocket']
    });
    
    socket.on('connect', () => {
      setIsConnected(true);
    });
    
    socket.on('new_message', (data) => {
      // Real-time message from bot or user
      if (selectedChat && data.lead_id === selectedChat.lead_id) {
        setMessages(prev => [...prev, data.message]);
        
        // Play notification sound
        const audio = new Audio('/sounds/message.mp3');
        audio.play().catch(() => {});
      }
      
      // Update active chats list
      setActiveChats(prev => 
        prev.map(chat => 
          chat.lead_id === data.lead_id 
            ? { ...chat, last_message: data.message.text, unread: true }
            : chat
        )
      );
    });
    
    socket.on('chat_taken_over', (data) => {
      if (selectedChat && data.lead_id === selectedChat.lead_id) {
        setIsTakenOver(true);
      }
    });
    
    socket.on('chat_released', (data) => {
      if (selectedChat && data.lead_id === selectedChat.lead_id) {
        setIsTakenOver(false);
      }
    });
    
    socketRef.current = socket;
  };
  
  const loadActiveChats = async () => {
    try {
      const response = await getActiveChats();
      setActiveChats(response.data);
    } catch (error) {
      console.error('Failed to load active chats:', error);
    }
  };
  
  const loadChatHistory = async (leadId) => {
    try {
      const response = await getChatHistory(leadId);
      setMessages(response.data);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };
  
  const handleTakeover = async () => {
    if (!selectedChat) return;
    
    try {
      await takeoverChat(selectedChat.lead_id);
      setIsTakenOver(true);
      
      // Add system message
      setMessages(prev => [...prev, {
        type: 'system',
        text: '✋ You took over this chat. Bot is now paused.',
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Failed to takeover chat:', error);
      alert('Failed to takeover chat');
    }
  };
  
  const handleRelease = async () => {
    if (!selectedChat) return;
    
    try {
      await releaseChat(selectedChat.lead_id);
      setIsTakenOver(false);
      
      // Add system message
      setMessages(prev => [...prev, {
        type: 'system',
        text: '🤖 Bot resumed. Chat released.',
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Failed to release chat:', error);
      alert('Failed to release chat');
    }
  };
  
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedChat || !isTakenOver) return;
    
    try {
      await sendManualMessage(selectedChat.lead_id, newMessage);
      
      // Add to local messages
      setMessages(prev => [...prev, {
        type: 'agent',
        text: newMessage,
        timestamp: new Date().toISOString()
      }]);
      
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message');
    }
  };
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  return (
    <div className="flex h-[calc(100vh-200px)] gap-4">
      {/* Active Chats List */}
      <div className="w-1/3 bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4">
          <div className="flex items-center gap-2">
            <Eye className="w-5 h-5" />
            <h3 className="font-semibold">Live Chats</h3>
          </div>
          <p className="text-sm text-blue-100 mt-1">{activeChats.length} active conversations</p>
        </div>
        
        <div className="divide-y divide-gray-200 dark:divide-gray-700 overflow-y-auto max-h-[calc(100vh-300px)]">
          {activeChats.map(chat => (
            <div
              key={chat.lead_id}
              onClick={() => setSelectedChat(chat)}
              className={`p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                selectedChat?.lead_id === chat.lead_id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="font-semibold text-gray-900 dark:text-white">
                  {chat.lead_name || `Lead #${chat.lead_id}`}
                </span>
                {chat.is_taken_over && (
                  <span className="text-xs bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300 px-2 py-1 rounded">
                    Manual
                  </span>
                )}
              </div>
              
              <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                {chat.last_message}
              </p>
              
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-gray-500">
                  {new Date(chat.last_message_at).toLocaleTimeString()}
                </span>
                {chat.unread && (
                  <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
                )}
              </div>
            </div>
          ))}
          
          {activeChats.length === 0 && (
            <div className="p-8 text-center text-gray-400">
              <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No active chats</p>
            </div>
          )}
        </div>
      </div>
      
      {/* Chat Messages */}
      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow flex flex-col">
        {selectedChat ? (
          <>
            {/* Chat Header */}
            <div className="bg-gray-50 dark:bg-gray-900 p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white">
                    {selectedChat.lead_name || `Lead #${selectedChat.lead_id}`}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedChat.telegram_username}
                  </p>
                </div>
                
                {/* Takeover Button */}
                {isTakenOver ? (
                  <button
                    onClick={handleRelease}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                  >
                    <Bot className="w-4 h-4" />
                    Release to Bot
                  </button>
                ) : (
                  <button
                    onClick={handleTakeover}
                    className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors"
                  >
                    <Hand className="w-4 h-4" />
                    ✋ Takeover
                  </button>
                )}
              </div>
              
              {isTakenOver && (
                <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded text-sm text-orange-700 dark:text-orange-300">
                  ✋ You're in control. Bot is paused.
                </div>
              )}
            </div>
            
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg p-3 ${
                      msg.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : msg.type === 'bot'
                        ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                        : msg.type === 'agent'
                        ? 'bg-orange-600 text-white'
                        : 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 text-center'
                    }`}
                  >
                    {msg.type !== 'system' && (
                      <div className="text-xs opacity-70 mb-1">
                        {msg.type === 'bot' ? '🤖 Bot' : msg.type === 'agent' ? '👤 You' : 'User'}
                      </div>
                    )}
                    <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                    <div className="text-xs opacity-70 mt-1">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            
            {/* Input */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              {isTakenOver ? (
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                  <button
                    type="submit"
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    Send
                  </button>
                </form>
              ) : (
                <div className="text-center text-gray-500 dark:text-gray-400 py-2">
                  <Bot className="w-6 h-6 mx-auto mb-1 opacity-50" />
                  <p className="text-sm">Bot is handling this conversation</p>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>Select a chat to view conversation</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
