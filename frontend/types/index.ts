// Chat types
export interface Message {
  id: number;
  session_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  content_type: 'text' | 'multimodal';
  images?: string[];
  created_at: string;
  is_bookmarked: boolean;
}

export interface ChatSession {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  summary?: string;
}

export interface ChatSessionDetail extends ChatSession {
  messages: Message[];
}

// Prompt types
export interface PromptTemplate {
  id: number;
  tab_name: string;
  subtab_name: string;
  prompt_text: string;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface TabWithSubtabs {
  tab_name: string;
  subtabs: PromptTemplate[];
}

// Document types
export interface Document {
  id: number;
  filename: string;
  doc_type: 'resume' | 'jd' | 'other';
  content: string;
  session_id?: number;
  created_at: string;
}

// Setup profile types
export interface SetupProfile {
  id: number;
  name: string;
  prompt_ids: number[];
  created_at: string;
}

// Performance diagnostic types
export interface PerformanceDiagnostic {
  total_messages: number;
  system_messages: number;
  user_messages: number;
  assistant_messages: number;
  images_count: number;
  estimated_total_tokens: number;
  estimated_system_tokens: number;
  estimated_conversation_tokens: number;
  estimated_image_tokens: number;
  optimization_mode: boolean;
  will_send_messages: number;
  will_send_tokens: number;
  has_summary: boolean;
  issues: string[];
  recommendations: string[];
}

// WebSocket message types
export interface WSMessage {
  type: 'user_message' | 'stream_start' | 'stream_chunk' | 'stream_end' | 'error' | 'stopped' | 'pong';
  message_id?: number;
  content?: string;
  full_content?: string;
  message?: string;
}

// Audio types
export interface TranscriptionResult {
  text: string;
  success: boolean;
  error?: string;
  duration?: number;
}

// Model types
export type ModelType = 'gpt-4o' | 'gpt-4o-mini' | 'gpt-4-turbo';
export type AnswerMode = 'default' | 'quick' | 'detailed' | 'code';

// App state types
export interface AppSettings {
  model: ModelType;
  answerMode: AnswerMode;
  optimizationMode: boolean;
  fontSize: number;
}




