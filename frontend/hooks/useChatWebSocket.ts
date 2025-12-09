'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { createChatWebSocket } from '@/lib/api';
import type { WSMessage, ModelType, AnswerMode } from '@/types';

interface UseChatWebSocketReturn {
  isConnected: boolean;
  isStreaming: boolean;
  streamingContent: string;
  sendMessage: (content: string, images?: string[], model?: ModelType, answerMode?: AnswerMode) => void;
  stopStreaming: () => void;
  connect: () => void;
  disconnect: () => void;
}

interface UseChatWebSocketOptions {
  sessionId: number;
  onMessageComplete?: (messageId: number, content: string) => void;
  onUserMessageSent?: (messageId: number) => void;
  onError?: (error: string) => void;
}

export function useChatWebSocket(options: UseChatWebSocketOptions): UseChatWebSocketReturn {
  const { sessionId, onMessageComplete, onUserMessageSent, onError } = options;
  
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    try {
      const ws = createChatWebSocket(sessionId);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'ping' }));
          }
        }, 30000);
      };
      
      ws.onmessage = (event) => {
        try {
          const data: WSMessage = JSON.parse(event.data);
          
          switch (data.type) {
            case 'user_message':
              if (data.message_id && onUserMessageSent) {
                onUserMessageSent(data.message_id);
              }
              break;
              
            case 'stream_start':
              setIsStreaming(true);
              setStreamingContent('');
              break;
              
            case 'stream_chunk':
              if (data.content) {
                setStreamingContent(prev => prev + data.content);
              }
              break;
              
            case 'stream_end':
              setIsStreaming(false);
              if (data.message_id && data.full_content && onMessageComplete) {
                onMessageComplete(data.message_id, data.full_content);
              }
              setStreamingContent('');
              break;
              
            case 'error':
              setIsStreaming(false);
              if (onError) {
                onError(data.message || 'Unknown error');
              }
              break;
              
            case 'stopped':
              setIsStreaming(false);
              break;
              
            case 'pong':
              // Connection alive
              break;
          }
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setIsStreaming(false);
        
        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) {
          onError('WebSocket connection error');
        }
      };
      
      wsRef.current = ws;
      
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      if (onError) {
        onError('Failed to connect');
      }
    }
  }, [sessionId, onMessageComplete, onUserMessageSent, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setIsStreaming(false);
  }, []);

  const sendMessage = useCallback((
    content: string,
    images?: string[],
    model: ModelType = 'gpt-4o',
    answerMode: AnswerMode = 'default'
  ) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      if (onError) {
        onError('Not connected to server');
      }
      return;
    }
    
    const message = {
      action: 'message',
      content,
      images,
      model,
      answer_mode: answerMode,
      optimization_mode: true,
    };
    
    wsRef.current.send(JSON.stringify(message));
  }, [onError]);

  const stopStreaming = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'stop' }));
    }
    setIsStreaming(false);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  // Reconnect on session change
  useEffect(() => {
    disconnect();
    connect();
  }, [sessionId, connect, disconnect]);

  return {
    isConnected,
    isStreaming,
    streamingContent,
    sendMessage,
    stopStreaming,
    connect,
    disconnect,
  };
}




