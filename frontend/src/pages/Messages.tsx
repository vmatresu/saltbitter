import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useRequireAuth } from '../hooks/useAuth';
import { useWebSocket } from '../hooks/useWebSocket';
import apiClient from '../api/client';
import { MessageList } from '../components/MessageList';

interface Conversation {
  user_id: string;
  name: string;
  photo: string;
  last_message: string;
  last_message_time: string;
  unread_count: number;
}

export const Messages: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const { isAuthenticated, isLoading: authLoading } = useRequireAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const { onMessage } = useWebSocket();

  useEffect(() => {
    if (isAuthenticated) {
      loadConversations();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    const cleanup = onMessage((data) => {
      // Refresh conversations when new message arrives
      loadConversations();
    });

    return cleanup;
  }, [onMessage]);

  const loadConversations = async () => {
    try {
      const data = await apiClient.getConversations();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading messages...</p>
        </div>
      </div>
    );
  }

  // If userId is specified, show the chat view
  if (userId) {
    return <MessageList userId={userId} />;
  }

  // Otherwise, show conversations list
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Messages</h1>
          <button
            onClick={() => navigate('/matches')}
            className="btn-primary"
          >
            Back to Matches
          </button>
        </div>

        <div className="card">
          {conversations.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No conversations yet</p>
              <p className="text-gray-500 text-sm">
                Start matching to begin conversations!
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {conversations.map((conversation) => (
                <div
                  key={conversation.user_id}
                  onClick={() => navigate(`/messages/${conversation.user_id}`)}
                  className="flex items-center p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <img
                    src={conversation.photo || '/default-avatar.png'}
                    alt={conversation.name}
                    className="w-14 h-14 rounded-full object-cover"
                  />
                  <div className="ml-4 flex-1">
                    <div className="flex justify-between items-start">
                      <h3 className="font-semibold text-gray-900">{conversation.name}</h3>
                      <span className="text-xs text-gray-500">
                        {new Date(conversation.last_message_time).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 truncate">{conversation.last_message}</p>
                  </div>
                  {conversation.unread_count > 0 && (
                    <div className="ml-2 bg-primary text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                      {conversation.unread_count}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Messages;
