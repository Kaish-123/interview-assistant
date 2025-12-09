'use client';

import { useEffect, useRef, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface HotkeyEvent {
  type: 'hotkey' | 'keepalive';
  key?: string;
  action?: string;
  timestamp: number;
}

interface HotkeyHandlers {
  onToggleRecording?: () => void;
  onScrollBottom?: () => void;
  onScrollTop?: () => void;
  onSaveLayout?: () => void;
  onCancelAction?: () => void;
}

export function useGlobalHotkeys(handlers: HotkeyHandlers) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const handlersRef = useRef(handlers);
  
  // Keep handlers ref updated
  useEffect(() => {
    handlersRef.current = handlers;
  }, [handlers]);
  
  const handleHotkeyEvent = useCallback((event: HotkeyEvent) => {
    if (event.type !== 'hotkey') return;
    
    console.log('🎹 Global hotkey received:', event.action);
    
    const currentHandlers = handlersRef.current;
    
    switch (event.action) {
      case 'toggle_recording':
        currentHandlers.onToggleRecording?.();
        break;
      case 'scroll_bottom':
        currentHandlers.onScrollBottom?.();
        break;
      case 'scroll_top':
        currentHandlers.onScrollTop?.();
        break;
      case 'save_layout':
        currentHandlers.onSaveLayout?.();
        break;
      case 'cancel_action':
        currentHandlers.onCancelAction?.();
        break;
      default:
        console.log('Unknown hotkey action:', event.action);
    }
  }, []);
  
  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Clear any pending reconnect
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    try {
      const wsUrl = API_BASE.replace('http', 'ws');
      const ws = new WebSocket(`${wsUrl}/hotkeys/ws`);
      
      ws.onopen = () => {
        console.log('🎹 Global hotkeys WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as HotkeyEvent;
          handleHotkeyEvent(data);
        } catch (e) {
          console.error('Failed to parse hotkey event:', e);
        }
      };
      
      ws.onerror = (error) => {
        console.error('Hotkey WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('🎹 Global hotkeys WebSocket disconnected');
        wsRef.current = null;
        
        // Reconnect after delay
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('🔄 Reconnecting hotkeys WebSocket...');
          connect();
        }, 3000);
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect hotkeys WebSocket:', error);
      
      // Retry connection
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    }
  }, [handleHotkeyEvent]);
  
  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);
  
  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}

export default useGlobalHotkeys;

