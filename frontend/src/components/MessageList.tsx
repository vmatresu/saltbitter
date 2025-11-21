import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import apiClient from '../api/client';

interface Message {
  id: string;
  from_user_id: string;
  to_user_id: string;
  content: string;
  sent_at: string;
}

interface MessageListProps {
  userId: string;
}

export const MessageList: React.FC<MessageListProps> = ({ userId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [userInfo, setUserInfo] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { sendMessage, onMessage } = useWebSocket();

  const currentUserId = localStorage.getItem('user_id') || '';

  useEffect(() => {
    loadMessages();
    loadUserInfo();
  }, [userId]);

  useEffect(() => {
    const cleanup = onMessage((data) => {
      if (data.from_user_id === userId || data.to_user_id === userId) {
        setMessages((prev) => [...prev, data]);
        scrollToBottom();
      }
    });

    return cleanup;
  }, [userId, onMessage]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadMessages = async () => {
    try {
      const data = await apiClient.getMessages(userId);
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserInfo = async () => {
    try {
      const data = await apiClient.getProfile(userId);
      setUserInfo(data);
    } catch (error) {
      console.error('Failed to load user info:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      // Optimistically add message to UI
      const tempMessage: Message = {
        id: `temp-${Date.now()}`,
        from_user_id: currentUserId,
        to_user_id: userId,
        content: newMessage,
        sent_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempMessage]);
      setNewMessage('');

      // Send via WebSocket
      sendMessage(userId, newMessage);

      // Also send via REST API as backup
      await apiClient.sendMessage(userId, newMessage);
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading messages...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <button
            onClick={() => navigate('/messages')}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {userInfo && (
            <>
              <img
                src={userInfo.photos?.[0] || '/default-avatar.png'}
                alt={userInfo.name}
                className="w-10 h-10 rounded-full object-cover"
              />
              <div className="flex-1">
                <h2 className="font-semibold text-gray-900">{userInfo.name}</h2>
                <p className="text-sm text-gray-500">Online</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
          {messages.map((message) => {
            const isFromMe = message.from_user_id === currentUserId;
            return (
              <div key={message.id} className={`flex ${isFromMe ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-xs md:max-w-md px-4 py-2 rounded-2xl ${
                    isFromMe
                      ? 'bg-primary text-white rounded-br-none'
                      : 'bg-white text-gray-900 border border-gray-200 rounded-bl-none'
                  }`}
                >
                  <p className="break-words">{message.content}</p>
                  <p
                    className={`text-xs mt-1 ${
                      isFromMe ? 'text-purple-200' : 'text-gray-500'
                    }`}
                  >
                    {new Date(message.sent_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="input-field flex-1"
          />
          <button
            type="submit"
            disabled={!newMessage.trim()}
            className="btn-primary px-6"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default MessageList;
