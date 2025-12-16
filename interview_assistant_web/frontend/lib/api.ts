/**
 * API Client for Interview Assistant Backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Generic fetch wrapper
// ============================================================================

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, config);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || error.detail || 'Request failed');
  }
  
  return response.json();
}

// ============================================================================
// Chat API
// ============================================================================

export const chatAPI = {
  // Sessions
  async createSession(title?: string, systemPrompt?: string) {
    return fetchAPI<{ id: number; title: string }>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({ title, system_prompt: systemPrompt }),
    });
  },

  async getSessions() {
    return fetchAPI<Array<{
      id: number;
      title: string;
      created_at: string;
      updated_at: string;
      message_count: number;
    }>>('/chat/sessions');
  },

  async getSession(sessionId: number) {
    return fetchAPI<{
      id: number;
      title: string;
      messages: Array<{
        id: number;
        role: string;
        content: string;
        images?: string[];
        is_bookmarked: boolean;
        created_at: string;
      }>;
    }>(`/chat/sessions/${sessionId}`);
  },

  async updateSessionTitle(sessionId: number, title: string) {
    return fetchAPI<{ success: boolean }>(`/chat/sessions/${sessionId}/title?title=${encodeURIComponent(title)}`, {
      method: 'PUT',
    });
  },

  async deleteSession(sessionId: number) {
    return fetchAPI<{ success: boolean }>(`/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  },

  // Messages
  async addMessage(sessionId: number, role: string, content: string, images?: string[]) {
    return fetchAPI<{ id: number }>(`/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ role, content, images }),
    });
  },

  // Bookmarks
  async toggleBookmark(messageId: number, isBookmarked: boolean) {
    return fetchAPI<{ success: boolean }>('/chat/bookmarks/toggle', {
      method: 'POST',
      body: JSON.stringify({ message_id: messageId, is_bookmarked: isBookmarked }),
    });
  },

  async getBookmarks(sessionId: number) {
    return fetchAPI<Array<{
      id: number;
      content: string;
      created_at: string;
    }>>(`/chat/sessions/${sessionId}/bookmarks`);
  },

  // Diagnostics
  async getDiagnostics(sessionId: number) {
    return fetchAPI<{
      total_messages: number;
      will_send_tokens: number;
      issues: string[];
      recommendations: string[];
    }>(`/chat/sessions/${sessionId}/diagnostics`);
  },

  // Summarize
  async summarizeSession(sessionId: number) {
    return fetchAPI<{ summary: string }>(`/chat/sessions/${sessionId}/summarize`, {
      method: 'POST',
    });
  },

  // Quick setup
  async quickSetup(sessionId: number, promptIds: number[], additionalText?: string, images?: string[]) {
    return fetchAPI<{ success: boolean; prompts_applied: number }>(`/chat/sessions/${sessionId}/quick-setup`, {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        prompt_ids: promptIds,
        additional_text: additionalText,
        images,
      }),
    });
  },
};

// ============================================================================
// Audio API
// ============================================================================

export const audioAPI = {
  async transcribe(audioData: string, format: string = 'webm', prompt?: string) {
    return fetchAPI<{
      text: string;
      success: boolean;
      error?: string;
    }>('/audio/transcribe', {
      method: 'POST',
      body: JSON.stringify({ audio_data: audioData, format, prompt }),
    });
  },
};

// ============================================================================
// Documents API
// ============================================================================

export const documentsAPI = {
  async upload(file: File, docType: string = 'resume', sessionId?: number) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);
    if (sessionId) formData.append('session_id', String(sessionId));

    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Upload failed' }));
      throw new Error(error.error || error.detail || 'Upload failed');
    }

    return response.json();
  },

  async getDocuments(docType?: string) {
    const params = docType ? `?doc_type=${docType}` : '';
    return fetchAPI<Array<{
      id: number;
      filename: string;
      doc_type: string;
      content: string;
      created_at: string;
    }>>(`/documents${params}`);
  },

  async deleteDocument(documentId: number) {
    return fetchAPI<{ success: boolean }>(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  },

  async addToSession(documentId: number, sessionId: number) {
    return fetchAPI<{ success: boolean }>(`/documents/${documentId}/add-to-session?session_id=${sessionId}`, {
      method: 'POST',
    });
  },
};

// ============================================================================
// Prompts API
// ============================================================================

export const promptsAPI = {
  async getGroupedTemplates() {
    return fetchAPI<Array<{
      tab_name: string;
      subtabs: Array<{
        id: number;
        subtab_name: string;
        prompt_text: string;
      }>;
    }>>('/prompts/templates/grouped');
  },

  async getAllTemplates() {
    return fetchAPI<Array<{
      id: number;
      tab_name: string;
      subtab_name: string;
      prompt_text: string;
    }>>('/prompts/templates');
  },

  async createTemplate(tabName: string, subtabName: string, promptText: string) {
    return fetchAPI<{ id: number }>('/prompts/templates', {
      method: 'POST',
      body: JSON.stringify({
        tab_name: tabName,
        subtab_name: subtabName,
        prompt_text: promptText,
      }),
    });
  },

  async updateTemplate(templateId: number, data: { subtab_name?: string; prompt_text?: string }) {
    return fetchAPI<{ id: number }>(`/prompts/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deleteTemplate(templateId: number) {
    return fetchAPI<{ success: boolean }>(`/prompts/templates/${templateId}`, {
      method: 'DELETE',
    });
  },

  async moveTemplate(templateId: number, newTabName: string) {
    return fetchAPI<{ id: number }>(`/prompts/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify({ tab_name: newTabName }),
    });
  },

  async renameFolder(oldName: string, newName: string) {
    return fetchAPI<{ success: boolean; templates_updated: number }>(
      `/prompts/tabs/${encodeURIComponent(oldName)}/rename?new_name=${encodeURIComponent(newName)}`,
      { method: 'PUT' }
    );
  },

  async deleteFolder(folderName: string) {
    return fetchAPI<{ success: boolean; templates_deleted: number }>(
      `/prompts/tabs/${encodeURIComponent(folderName)}`,
      { method: 'DELETE' }
    );
  },

  // Profiles
  async getProfiles() {
    return fetchAPI<Array<{
      id: number;
      name: string;
      prompt_ids: number[];
    }>>('/prompts/profiles');
  },

  async createProfile(name: string, promptIds: number[]) {
    return fetchAPI<{ id: number }>('/prompts/profiles', {
      method: 'POST',
      body: JSON.stringify({ name, prompt_ids: promptIds }),
    });
  },

  async deleteProfile(profileId: number) {
    return fetchAPI<{ success: boolean }>(`/prompts/profiles/${profileId}`, {
      method: 'DELETE',
    });
  },

  // Import/Export
  async exportTemplates() {
    return fetchAPI<{ templates: any[]; profiles: any[] }>('/prompts/export');
  },

  async importTemplates(data: { templates: any[] }) {
    return fetchAPI<{ imported: number }>('/prompts/import', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

// ============================================================================
// Status API
// ============================================================================

export const statusAPI = {
  async getStatus() {
    return fetchAPI<{
      api: string;
      database: string;
      openai: string;
    }>('/api/status');
  },

  async getModels() {
    return fetchAPI<{
      models: Record<string, { name: string; description: string }>;
      default: string;
    }>('/api/models');
  },
};

// ============================================================================
// WebSocket helpers
// ============================================================================

export function createChatWebSocket(sessionId: number): WebSocket {
  const wsUrl = API_BASE.replace('http', 'ws');
  return new WebSocket(`${wsUrl}/chat/ws/${sessionId}`);
}

export function createAudioWebSocket(): WebSocket {
  const wsUrl = API_BASE.replace('http', 'ws');
  return new WebSocket(`${wsUrl}/audio/ws/transcribe`);
}



