'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Bot } from 'lucide-react';
import Sidebar from '@/components/Sidebar';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';
import ControlBar from '@/components/ControlBar';
import QuickSetupModal from '@/components/QuickSetupModal';
import DiagnosticsModal from '@/components/DiagnosticsModal';
import BookmarksModal from '@/components/BookmarksModal';
import HotkeysHelpModal from '@/components/HotkeysHelpModal';
import { chatAPI, documentsAPI, statusAPI, createChatWebSocket } from '@/lib/api';
import { useStore } from '@/hooks/useStore';
import { useHotkeys } from '@/hooks/useHotkeys';
import { useGlobalHotkeys } from '@/hooks/useGlobalHotkeys';
import type { Message, ChatSession, ModelType, AnswerMode, WSMessage } from '@/types';
import { cn } from '@/lib/utils';

export default function Home() {
  // Global state from store
  const {
    currentSessionId,
    setCurrentSession,
    messages,
    setMessages,
    addMessage,
    updateMessage,
    sessions,
    setSessions,
    addSession,
    removeSession,
    model,
    setModel,
    answerMode,
    setAnswerMode,
    optimizationMode,
    setOptimizationMode,
    fontSize,
    setFontSize,
    sidebarOpen,
    setSidebarOpen,
    isStreaming,
    setIsStreaming,
    apiConnected,
    setApiConnected,
    pendingImages,
    addPendingImage,
    clearPendingImages,
  } = useStore();

  // Local state
  const [streamingContent, setStreamingContent] = useState('');
  const [showQuickSetup, setShowQuickSetup] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [showBookmarks, setShowBookmarks] = useState(false);
  const [showHotkeysHelp, setShowHotkeysHelp] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  // Hotkey triggers for audio recording
  const [listenExternalTrigger, setListenExternalTrigger] = useState(0);
  const [listenInternalTrigger, setListenInternalTrigger] = useState(0);
  
  // Sidebar width state (resizable) - will be loaded from localStorage
  const [sidebarWidth, setSidebarWidth] = useState(288); // Default 288px (w-72)
  
  // Chat input height state (resizable) - will be loaded from localStorage
  const [chatInputHeight, setChatInputHeight] = useState(140); // Default 140px
  
  // Layout saved notification
  const [layoutSavedNotification, setLayoutSavedNotification] = useState(false);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatInputRef = useRef<HTMLTextAreaElement>(null);
  
  // Scroll functions for hotkeys
  const scrollToBottom = useCallback(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, []);
  
  const scrollToTop = useCallback(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  }, []);
  
  // UI Layout storage key
  const LAYOUT_STORAGE_KEY = 'interview_assistant_layout';
  
  // Save UI layout to localStorage (F2)
  const saveLayout = useCallback(() => {
    const layout = {
      sidebarWidth,
      chatInputHeight,
      sidebarOpen,
      fontSize,
      timestamp: Date.now(),
    };
    
    try {
      localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(layout));
      console.log('💾 UI Layout saved:', layout);
      
      // Show notification
      setLayoutSavedNotification(true);
      setTimeout(() => setLayoutSavedNotification(false), 2000);
    } catch (error) {
      console.error('Failed to save layout:', error);
    }
  }, [sidebarWidth, chatInputHeight, sidebarOpen, fontSize]);
  
  // Load UI layout from localStorage on startup
  useEffect(() => {
    try {
      const savedLayout = localStorage.getItem(LAYOUT_STORAGE_KEY);
      if (savedLayout) {
        const layout = JSON.parse(savedLayout);
        console.log('📂 Loading saved UI layout:', layout);
        
        if (layout.sidebarWidth) setSidebarWidth(layout.sidebarWidth);
        if (layout.chatInputHeight) setChatInputHeight(layout.chatInputHeight);
        if (typeof layout.sidebarOpen === 'boolean') setSidebarOpen(layout.sidebarOpen);
        if (layout.fontSize) setFontSize(layout.fontSize);
      }
    } catch (error) {
      console.error('Failed to load layout:', error);
    }
  }, []); // Run once on mount

  // Available models for cycling
  const availableModels: ModelType[] = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'];

  // =========================================
  // HOTKEYS INTEGRATION
  // =========================================
  useHotkeys({
    // Recording controls - these will be passed down to ChatInput
    onToggleRecording: () => {
      // This is handled by ChatInput component
      const recordBtn = document.querySelector('[title="Start recording"], [title="Stop recording"]') as HTMLButtonElement;
      recordBtn?.click();
    },
    onStopRecording: () => {
      const recordBtn = document.querySelector('[title="Stop recording"]') as HTMLButtonElement;
      recordBtn?.click();
    },
    
    // 5+6: Listen with External Mic (microphone for your voice)
    onListenExternal: () => {
      console.log('🎧 5+6 Hotkey: Triggering external mic recording');
      setListenExternalTrigger(prev => prev + 1);
    },
    
    // 4+5: Listen with Internal Audio (BlackHole for Zoom/system audio)
    onListenInternal: () => {
      console.log('🔊 4+5 Hotkey: Triggering internal audio recording (BlackHole)');
      setListenInternalTrigger(prev => prev + 1);
    },
    
    // Screenshot - trigger file input for image
    onCaptureScreenshot: async () => {
      try {
        // Try to use clipboard API to paste screenshot
        const clipboardItems = await navigator.clipboard.read();
        for (const item of clipboardItems) {
          if (item.types.includes('image/png') || item.types.includes('image/jpeg')) {
            const blob = await item.getType(item.types.find(t => t.startsWith('image/')) || 'image/png');
            const reader = new FileReader();
            reader.onloadend = () => {
              const base64 = reader.result as string;
              addPendingImage(base64);
            };
            reader.readAsDataURL(blob);
            return;
          }
        }
        alert('📸 Take a screenshot (Cmd+Shift+4) and press Shift+1 again to paste');
      } catch {
        alert('📸 Take a screenshot (Cmd+Shift+4) and paste with Cmd+V');
      }
    },
    
    // Navigation
    onFocusInput: () => {
      // Close any open modals first
      setShowQuickSetup(false);
      setShowDiagnostics(false);
      setShowBookmarks(false);
      setShowHotkeysHelp(false);
      // Focus the chat input
      const textarea = document.querySelector('textarea[placeholder*="Type your message"]') as HTMLTextAreaElement;
      textarea?.focus();
    },
    
    onUploadResume: () => {
      fileInputRef.current?.click();
    },
    
    onQuickSetup: () => setShowQuickSetup(true),
    
    onNewChat: async () => {
      await handleNewSession(); // Uses timestamp title by default
    },
    
    // Font size
    onIncreaseFontSize: () => setFontSize(Math.min(fontSize + 2, 24)),
    onDecreaseFontSize: () => setFontSize(Math.max(fontSize - 2, 10)),
    
    // Bookmarks
    onAddBookmark: () => {
      // Bookmark the last assistant message
      const assistantMessages = messages.filter(m => m.role === 'assistant');
      if (assistantMessages.length > 0) {
        const lastMsg = assistantMessages[assistantMessages.length - 1];
        if (!lastMsg.is_bookmarked) {
          handleToggleBookmark(lastMsg.id, true);
        }
      }
    },
    onToggleBookmarks: () => setShowBookmarks(!showBookmarks),
    
    // Model & Settings
    onToggleModel: () => {
      const currentIndex = availableModels.indexOf(model);
      const nextIndex = (currentIndex + 1) % availableModels.length;
      setModel(availableModels[nextIndex]);
    },
    onToggleOptimization: () => setOptimizationMode(!optimizationMode),
    onToggleDiagnostics: () => setShowDiagnostics(true),
    
    // Other
    onToggleSidebar: () => setSidebarOpen(!sidebarOpen),
    onCopyLastResponse: () => {
      const assistantMessages = messages.filter(m => m.role === 'assistant');
      if (assistantMessages.length > 0) {
        const lastMsg = assistantMessages[assistantMessages.length - 1];
        navigator.clipboard.writeText(typeof lastMsg.content === 'string' ? lastMsg.content : '');
        // Show a brief notification
        alert('📋 Last response copied to clipboard!');
      }
    },
    onClearChat: () => {
      if (confirm('Are you sure you want to clear the current chat?')) {
        setMessages([]);
      }
    },
    
    // Chat scroll navigation
    onScrollToBottom: scrollToBottom,
    onScrollToTop: scrollToTop,
    
    // UI Layout
    onSaveLayout: saveLayout,
  });

  // Show hotkeys help with ? key
  useEffect(() => {
    const handleQuestionMark = (e: KeyboardEvent) => {
      if (e.key === '?' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
        e.preventDefault();
        setShowHotkeysHelp(true);
      }
    };
    window.addEventListener('keydown', handleQuestionMark);
    return () => window.removeEventListener('keydown', handleQuestionMark);
  }, []);

  // =========================================
  // GLOBAL HOTKEYS (Work even outside browser focus!)
  // =========================================
  // Ref for recording trigger from global hotkeys
  const triggerRecordingRef = useRef<(() => void) | null>(null);
  
  useGlobalHotkeys({
    onToggleRecording: () => {
      console.log('🎹 Global toggle recording triggered');
      // Click the recording button programmatically
      const recordBtn = document.querySelector('[data-recording-button]') as HTMLButtonElement;
      if (recordBtn) {
        recordBtn.click();
      } else {
        // Fallback: trigger via title
        const btn = document.querySelector('[title*="recording"]') as HTMLButtonElement;
        btn?.click();
      }
    },
    onScrollBottom: () => {
      console.log('🎹 Global scroll bottom triggered');
      scrollToBottom();
    },
    onScrollTop: () => {
      console.log('🎹 Global scroll top triggered');
      scrollToTop();
    },
    onSaveLayout: () => {
      console.log('🎹 Global save layout triggered');
      saveLayout();
    },
    onCancelAction: () => {
      console.log('🎹 Global cancel action triggered');
      if (isStreaming) {
        handleStopStreaming();
      }
    },
  });

  // Check API status on mount
  useEffect(() => {
    checkApiStatus();
    loadSessions();
  }, []);

  // Connect WebSocket when session changes
  useEffect(() => {
    if (currentSessionId) {
      connectWebSocket(currentSessionId);
      loadSessionMessages(currentSessionId);
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [currentSessionId]);

  // NOTE: Auto-scroll disabled - user prefers manual scrolling during interviews
  // Uncomment below if you want auto-scroll behavior
  // useEffect(() => {
  //   messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  // }, [messages, streamingContent]);

  const checkApiStatus = async () => {
    try {
      const status = await statusAPI.getStatus();
      const connected = status.openai === 'connected' || status.api === 'running';
      setApiConnected(connected);
      setIsLoading(false);
    } catch (error) {
      console.error('API status check failed:', error);
      // If backend is running but OpenAI check failed, still allow usage
      // The actual API calls will show specific errors
      setApiConnected(true); // Allow usage, errors will show in chat
      setIsLoading(false);
    }
  };

  const loadSessions = async () => {
    try {
      const data = await chatAPI.getSessions();
      setSessions(data as ChatSession[]);
      
      // Select most recent session if none selected
      if (!currentSessionId && data.length > 0) {
        setCurrentSession(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadSessionMessages = async (sessionId: number) => {
    try {
      const data = await chatAPI.getSession(sessionId);
      setMessages(data.messages as Message[]);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const connectWebSocket = (sessionId: number) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = createChatWebSocket(sessionId);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data: WSMessage = JSON.parse(event.data);

        switch (data.type) {
          case 'user_message':
            // User message confirmed
            break;

          case 'stream_start':
            setIsStreaming(true);
            setStreamingContent('');
            break;

          case 'stream_chunk':
            if (data.content) {
              setStreamingContent((prev) => prev + data.content);
            }
            break;

          case 'stream_end':
            setIsStreaming(false);
            if (data.full_content && data.message_id) {
              // Add assistant message to state
              const assistantMessage: Message = {
                id: data.message_id,
                session_id: sessionId,
                role: 'assistant',
                content: data.full_content,
                content_type: 'text',
                created_at: new Date().toISOString(),
                is_bookmarked: false,
              };
              addMessage(assistantMessage);
            }
            setStreamingContent('');
            break;

          case 'error':
            setIsStreaming(false);
            setStreamingContent('');
            console.error('WebSocket error:', data.message);
            break;

          case 'stopped':
            setIsStreaming(false);
            break;
        }
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnect after delay
      setTimeout(() => {
        if (currentSessionId === sessionId) {
          connectWebSocket(sessionId);
        }
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  };

  const handleSendMessage = async (content: string, images?: string[]) => {
    let sessionId = currentSessionId;
    
    if (!sessionId) {
      // Create new session first with timestamp title
      try {
        const timestampTitle = generateTimestampTitle();
        const session = await chatAPI.createSession(timestampTitle);
        const newSession: ChatSession = {
          id: session.id,
          title: timestampTitle,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 0,
        };
        addSession(newSession);
        setCurrentSession(session.id);
        sessionId = session.id;
        
        // Connect WebSocket and wait for it to open
        await new Promise<void>((resolve, reject) => {
          const ws = createChatWebSocket(session.id);
          
          ws.onopen = () => {
            console.log('WebSocket connected for new session');
            wsRef.current = ws;
            
            // Set up other handlers
            ws.onmessage = (event) => {
              try {
                const data: WSMessage = JSON.parse(event.data);
                switch (data.type) {
                  case 'user_message':
                    break;
                  case 'stream_start':
                    setIsStreaming(true);
                    setStreamingContent('');
                    break;
                  case 'stream_chunk':
                    if (data.content) {
                      setStreamingContent((prev) => prev + data.content);
                    }
                    break;
                  case 'stream_end':
                    setIsStreaming(false);
                    if (data.full_content && data.message_id) {
                      const assistantMessage: Message = {
                        id: data.message_id,
                        session_id: session.id,
                        role: 'assistant',
                        content: data.full_content,
                        content_type: 'text',
                        created_at: new Date().toISOString(),
                        is_bookmarked: false,
                      };
                      addMessage(assistantMessage);
                    }
                    setStreamingContent('');
                    break;
                  case 'error':
                    setIsStreaming(false);
                    setStreamingContent('');
                    console.error('WebSocket error:', data.message);
                    break;
                  case 'stopped':
                    setIsStreaming(false);
                    break;
                }
              } catch (error) {
                console.error('WebSocket message parse error:', error);
              }
            };
            
            ws.onclose = () => {
              console.log('WebSocket disconnected');
            };
            
            ws.onerror = (error) => {
              console.error('WebSocket error:', error);
            };
            
            resolve();
          };
          
          ws.onerror = (error) => {
            console.error('Failed to connect WebSocket:', error);
            reject(error);
          };
          
          // Timeout after 5 seconds
          setTimeout(() => reject(new Error('WebSocket connection timeout')), 5000);
        });
      } catch (error) {
        console.error('Failed to create session:', error);
        return;
      }
    }

    // Add user message to UI immediately
    const userMessage: Message = {
      id: Date.now(), // Temporary ID
      session_id: sessionId,
      role: 'user',
      content,
      content_type: images ? 'multimodal' : 'text',
      images,
      created_at: new Date().toISOString(),
      is_bookmarked: false,
    };
    addMessage(userMessage);

    // Send via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('Sending message via WebSocket:', content.substring(0, 50));
      wsRef.current.send(
        JSON.stringify({
          action: 'message',
          content,
          images,
          model,
          answer_mode: answerMode,
          optimization_mode: optimizationMode,
        })
      );
      setIsStreaming(true);
    } else {
      console.error('WebSocket not connected (state: ' + wsRef.current?.readyState + '), cannot send message');
      // Try reconnecting
      connectWebSocket(sessionId);
    }
  };

  const handleStopStreaming = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'stop' }));
    }
    setIsStreaming(false);
  };

  // Generate timestamp title for chats
  const generateTimestampTitle = () => {
    const now = new Date();
    const options: Intl.DateTimeFormatOptions = {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    };
    return `Chat ${now.toLocaleDateString('en-US', options)}`;
  };

  // Extract filename without extension
  const getFileNameWithoutExtension = (filename: string) => {
    return filename.replace(/\.[^/.]+$/, '');
  };

  const handleNewSession = async (customTitle?: string | React.MouseEvent) => {
    try {
      // Ignore if customTitle is an event object (from button clicks)
      const title = (typeof customTitle === 'string') ? customTitle : generateTimestampTitle();
      const session = await chatAPI.createSession(title);
      const newSession: ChatSession = {
        id: session.id,
        title: title,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        message_count: 0,
      };
      addSession(newSession);
      setCurrentSession(session.id);
      setMessages([]);
      return session.id;
    } catch (error) {
      console.error('Failed to create session:', error);
      return null;
    }
  };

  const handleSelectSession = (sessionId: number) => {
    setCurrentSession(sessionId);
  };

  const handleDeleteSession = async (sessionId: number) => {
    try {
      await chatAPI.deleteSession(sessionId);
      removeSession(sessionId);
      if (currentSessionId === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const handleRenameSession = async (sessionId: number, newTitle: string) => {
    try {
      await chatAPI.updateSessionTitle(sessionId, newTitle);
      setSessions(
        sessions.map((s) => (s.id === sessionId ? { ...s, title: newTitle } : s))
      );
    } catch (error) {
      console.error('Failed to rename session:', error);
    }
  };

  const handleSelectPrompt = (promptText: string) => {
    // Send prompt directly
    handleSendMessage(promptText);
  };

  const handleUploadDocument = async () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      let sessionId = currentSessionId;
      const fileName = getFileNameWithoutExtension(file.name);
      
      // If no current session, create one with the filename as title
      if (!sessionId) {
        sessionId = await handleNewSession(fileName);
        if (!sessionId) {
          console.error('Failed to create session for document');
          return;
        }
      } else {
        // If current session exists and has default title, rename it to filename
        const currentSession = sessions.find(s => s.id === sessionId);
        if (currentSession && (
          currentSession.title === 'New Chat' || 
          currentSession.title.startsWith('Chat ') ||
          currentSession.message_count === 0
        )) {
          await chatAPI.updateSessionTitle(sessionId, fileName);
          // Update local state
          setSessions(sessions.map(s => 
            s.id === sessionId ? { ...s, title: fileName } : s
          ));
        }
      }
      
      await documentsAPI.upload(file, 'resume', sessionId);
      // Reload messages to show system message
      await loadSessionMessages(sessionId);
    } catch (error) {
      console.error('Failed to upload document:', error);
    }

    // Reset input
    e.target.value = '';
  };

  const handleToggleBookmark = async (messageId: number, isBookmarked: boolean) => {
    try {
      await chatAPI.toggleBookmark(messageId, isBookmarked);
      updateMessage(messageId, { is_bookmarked: isBookmarked });
    } catch (error) {
      console.error('Failed to toggle bookmark:', error);
    }
  };

  const handleQuickSetupApply = async (promptIds: number[], additionalText?: string) => {
    if (!currentSessionId) {
      await handleNewSession();
      return;
    }

    try {
      await chatAPI.quickSetup(currentSessionId, promptIds, additionalText);
      await loadSessionMessages(currentSessionId);
    } catch (error) {
      console.error('Failed to apply quick setup:', error);
    }
  };

  const handleSummarize = async () => {
    if (!currentSessionId) return;
    try {
      await chatAPI.summarizeSession(currentSessionId);
    } catch (error) {
      console.error('Failed to summarize:', error);
    }
  };

  const handleNavigateToMessage = (messageId: number) => {
    const element = document.getElementById(`message-${messageId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      element.classList.add('bookmark-highlight');
      setTimeout(() => {
        element.classList.remove('bookmark-highlight');
      }, 2000);
    }
  };

  const handleRemoveImage = (index: number) => {
    const newImages = [...pendingImages];
    newImages.splice(index, 1);
    clearPendingImages();
    newImages.forEach(addPendingImage);
  };

  // Filter out system messages for display
  const displayMessages = messages.filter((m) => m.role !== 'system');

  return (
    <div className="h-screen flex bg-dark-950">
      {/* Layout Saved Notification */}
      {layoutSavedNotification && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="px-4 py-2 bg-accent-green text-white rounded-lg shadow-lg flex items-center gap-2">
            <span>💾</span>
            <span className="font-medium">UI Layout Saved!</span>
            <span className="text-sm opacity-80">(Press F2 anytime to save)</span>
          </div>
        </div>
      )}
      
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
        onSelectPrompt={handleSelectPrompt}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        width={sidebarWidth}
        onWidthChange={setSidebarWidth}
        minWidth={180}
        maxWidth={450}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Control Bar */}
        <ControlBar
          model={model}
          answerMode={answerMode}
          optimizationMode={optimizationMode}
          fontSize={fontSize}
          apiConnected={apiConnected}
          onModelChange={setModel}
          onAnswerModeChange={setAnswerMode}
          onOptimizationToggle={() => setOptimizationMode(!optimizationMode)}
          onFontSizeChange={(delta) => setFontSize(Math.max(10, Math.min(24, fontSize + delta)))}
          onUploadDocument={handleUploadDocument}
          onShowDiagnostics={() => setShowDiagnostics(true)}
          onShowBookmarks={() => setShowBookmarks(true)}
          onQuickSetup={() => setShowQuickSetup(true)}
          onNewChat={handleNewSession}
          onShowHotkeys={() => setShowHotkeysHelp(true)}
        />

        {/* Messages Area */}
        <div ref={messagesContainerRef} className="flex-1 overflow-y-auto">
          {displayMessages.length === 0 && !isStreaming ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-4">
              <div className="w-16 h-16 bg-accent-blue/20 rounded-2xl flex items-center justify-center mb-4">
                <Bot className="w-8 h-8 text-accent-blue" />
              </div>
              <h2 className="text-xl font-semibold text-dark-100 mb-2">
                Interview Assistant
              </h2>
              <p className="text-dark-400 max-w-md">
                Start a new conversation, upload your resume, or use Quick Setup to prepare for your interview.
              </p>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleUploadDocument}
                  className="px-4 py-2 bg-dark-800 hover:bg-dark-700 text-dark-200 rounded-lg transition-colors"
                >
                  📁 Upload Resume/JD
                </button>
                <button
                  onClick={() => setShowQuickSetup(true)}
                  className="px-4 py-2 bg-accent-blue hover:bg-accent-blue/90 text-white rounded-lg transition-colors"
                >
                  🚀 Quick Setup
                </button>
              </div>
            </div>
          ) : (
            <>
              {displayMessages.map((message) => (
                <div key={message.id} id={`message-${message.id}`}>
                  <ChatMessage
                    message={message}
                    onToggleBookmark={handleToggleBookmark}
                    fontSize={fontSize}
                  />
                </div>
              ))}

              {/* Streaming message */}
              {isStreaming && streamingContent && (
                <ChatMessage
                  message={{
                    id: -1,
                    session_id: currentSessionId || 0,
                    role: 'assistant',
                    content: streamingContent,
                    content_type: 'text',
                    created_at: new Date().toISOString(),
                    is_bookmarked: false,
                  }}
                  fontSize={fontSize}
                />
              )}

              {/* Typing indicator */}
              {isStreaming && !streamingContent && (
                <div className="py-6 px-4 md:px-8 bg-dark-900">
                  <div className="max-w-4xl mx-auto flex gap-4">
                    <div className="w-8 h-8 bg-accent-green rounded-lg flex items-center justify-center flex-shrink-0">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-dark-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-dark-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-dark-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Chat Input */}
        <ChatInput
          onSend={handleSendMessage}
          onStop={handleStopStreaming}
          isStreaming={isStreaming}
          pendingImages={pendingImages}
          onAddImage={addPendingImage}
          onRemoveImage={handleRemoveImage}
          onClearImages={clearPendingImages}
          disabled={false}
          listenExternalTrigger={listenExternalTrigger}
          listenInternalTrigger={listenInternalTrigger}
          inputHeight={chatInputHeight}
          onInputHeightChange={setChatInputHeight}
          minInputHeight={100}
          maxInputHeight={350}
        />
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt"
        onChange={handleFileUpload}
        className="hidden"
      />

      {/* Modals */}
      <QuickSetupModal
        isOpen={showQuickSetup}
        onClose={() => setShowQuickSetup(false)}
        onApply={handleQuickSetupApply}
      />

      <DiagnosticsModal
        isOpen={showDiagnostics}
        onClose={() => setShowDiagnostics(false)}
        sessionId={currentSessionId}
        onSummarize={handleSummarize}
        onNewChat={handleNewSession}
      />

      <BookmarksModal
        isOpen={showBookmarks}
        onClose={() => setShowBookmarks(false)}
        sessionId={currentSessionId}
        onNavigateToMessage={handleNavigateToMessage}
        onRemoveBookmark={(id) => updateMessage(id, { is_bookmarked: false })}
      />

      <HotkeysHelpModal
        isOpen={showHotkeysHelp}
        onClose={() => setShowHotkeysHelp(false)}
      />
    </div>
  );
}

