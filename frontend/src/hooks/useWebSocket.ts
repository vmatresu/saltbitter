import { useEffect, useCallback } from 'react';
import { wsClient } from '../utils/websocket';

export const useWebSocket = () => {
  const connect = useCallback((token: string) => {
    wsClient.connect(token);
  }, []);

  const disconnect = useCallback(() => {
    wsClient.disconnect();
  }, []);

  const sendMessage = useCallback((toUserId: string, content: string) => {
    wsClient.sendMessage(toUserId, content);
  }, []);

  const onMessage = useCallback((callback: (data: any) => void) => {
    wsClient.on('message', callback);
    return () => wsClient.off('message', callback);
  }, []);

  const onMatch = useCallback((callback: (data: any) => void) => {
    wsClient.on('match', callback);
    return () => wsClient.off('match', callback);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      connect(token);
    }

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connect,
    disconnect,
    sendMessage,
    onMessage,
    onMatch,
  };
};
