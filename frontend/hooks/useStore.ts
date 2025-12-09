'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Message, ChatSession, PromptTemplate, ModelType, AnswerMode } from '@/types';

interface AppState {
  // Current session
  currentSessionId: number | null;
  messages: Message[];
  sessions: ChatSession[];
  
  // Settings
  model: ModelType;
  answerMode: AnswerMode;
  optimizationMode: boolean;
  fontSize: number;
  
  // UI state
  sidebarOpen: boolean;
  isRecording: boolean;
  isStreaming: boolean;
  liveTranscription: string;
  
  // Prompts
  promptTemplates: PromptTemplate[];
  
  // Connection status
  apiConnected: boolean;
  
  // Pending attachments (images)
  pendingImages: string[];
  
  // Actions
  setCurrentSession: (sessionId: number | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: number, content: Partial<Message>) => void;
  setSessions: (sessions: ChatSession[]) => void;
  addSession: (session: ChatSession) => void;
  removeSession: (sessionId: number) => void;
  
  setModel: (model: ModelType) => void;
  setAnswerMode: (mode: AnswerMode) => void;
  setOptimizationMode: (enabled: boolean) => void;
  setFontSize: (size: number) => void;
  
  setSidebarOpen: (open: boolean) => void;
  setIsRecording: (recording: boolean) => void;
  setIsStreaming: (streaming: boolean) => void;
  setLiveTranscription: (text: string) => void;
  
  setPromptTemplates: (templates: PromptTemplate[]) => void;
  
  setApiConnected: (connected: boolean) => void;
  
  addPendingImage: (image: string) => void;
  clearPendingImages: () => void;
  
  reset: () => void;
}

const initialState = {
  currentSessionId: null,
  messages: [],
  sessions: [],
  model: 'gpt-4o' as ModelType,
  answerMode: 'default' as AnswerMode,
  optimizationMode: true,
  fontSize: 14,
  sidebarOpen: true,
  isRecording: false,
  isStreaming: false,
  liveTranscription: '',
  promptTemplates: [],
  apiConnected: false,
  pendingImages: [],
};

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
      
      setMessages: (messages) => set({ messages }),
      
      addMessage: (message) => set((state) => ({
        messages: [...state.messages, message],
      })),
      
      updateMessage: (id, content) => set((state) => ({
        messages: state.messages.map((m) =>
          m.id === id ? { ...m, ...content } : m
        ),
      })),
      
      setSessions: (sessions) => set({ sessions }),
      
      addSession: (session) => set((state) => ({
        sessions: [session, ...state.sessions],
      })),
      
      removeSession: (sessionId) => set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
        currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId,
      })),
      
      setModel: (model) => set({ model }),
      setAnswerMode: (answerMode) => set({ answerMode }),
      setOptimizationMode: (optimizationMode) => set({ optimizationMode }),
      setFontSize: (fontSize) => set({ fontSize }),
      
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      setIsRecording: (isRecording) => set({ isRecording }),
      setIsStreaming: (isStreaming) => set({ isStreaming }),
      setLiveTranscription: (liveTranscription) => set({ liveTranscription }),
      
      setPromptTemplates: (promptTemplates) => set({ promptTemplates }),
      
      setApiConnected: (apiConnected) => set({ apiConnected }),
      
      addPendingImage: (image) => set((state) => ({
        pendingImages: [...state.pendingImages, image],
      })),
      
      clearPendingImages: () => set({ pendingImages: [] }),
      
      reset: () => set({
        ...initialState,
        // Preserve settings
        model: get().model,
        answerMode: get().answerMode,
        optimizationMode: get().optimizationMode,
        fontSize: get().fontSize,
      }),
    }),
    {
      name: 'interview-assistant-storage',
      partialize: (state) => ({
        model: state.model,
        answerMode: state.answerMode,
        optimizationMode: state.optimizationMode,
        fontSize: state.fontSize,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);




