'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  MessageSquare, 
  Plus, 
  ChevronRight, 
  ChevronDown, 
  Trash2, 
  Edit2,
  FileText,
  Bookmark,
  Settings,
  X,
  GripVertical,
  FolderPlus,
  MoreVertical,
  Move,
  Copy,
  Check
} from 'lucide-react';
import { cn, formatDate, truncate } from '@/lib/utils';
import { chatAPI, promptsAPI } from '@/lib/api';
import type { ChatSession, TabWithSubtabs } from '@/types';

interface SidebarProps {
  sessions: ChatSession[];
  currentSessionId: number | null;
  onSelectSession: (sessionId: number) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: number) => void;
  onRenameSession: (sessionId: number, newTitle: string) => void;
  onSelectPrompt: (promptText: string) => void;
  isOpen: boolean;
  onToggle: () => void;
  width?: number;
  onWidthChange?: (width: number) => void;
  minWidth?: number;
  maxWidth?: number;
}

export default function Sidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onRenameSession,
  onSelectPrompt,
  isOpen,
  onToggle,
  width = 288,
  onWidthChange,
  minWidth = 200,
  maxWidth = 500,
}: SidebarProps) {
  const [promptTabs, setPromptTabs] = useState<TabWithSubtabs[]>([]);
  const [expandedTabs, setExpandedTabs] = useState<Set<string>>(new Set());
  const [editingSession, setEditingSession] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [activeSection, setActiveSection] = useState<'chats' | 'prompts'>('chats');
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  
  // Prompt management state
  const [showAddFolder, setShowAddFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [showAddPrompt, setShowAddPrompt] = useState<string | null>(null); // folder name
  const [newPromptName, setNewPromptName] = useState('');
  const [newPromptText, setNewPromptText] = useState('');
  const [editingPrompt, setEditingPrompt] = useState<{id: number; name: string; text: string} | null>(null);
  const [editingFolder, setEditingFolder] = useState<string | null>(null);
  const [editFolderName, setEditFolderName] = useState('');
  const [promptMenu, setPromptMenu] = useState<{id: number; tabName: string} | null>(null);
  const [folderMenu, setFolderMenu] = useState<string | null>(null);
  const [showMovePrompt, setShowMovePrompt] = useState<{id: number; currentTab: string} | null>(null);

  // Handle resize drag
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = Math.min(maxWidth, Math.max(minWidth, e.clientX));
      onWidthChange?.(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, minWidth, maxWidth, onWidthChange]);

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      const data = await promptsAPI.getGroupedTemplates();
      setPromptTabs(data);
    } catch (error) {
      console.error('Failed to load prompts:', error);
    }
  };

  // Add new folder
  const handleAddFolder = async () => {
    if (!newFolderName.trim()) return;
    try {
      // Create a placeholder prompt to create the folder
      await promptsAPI.createTemplate(newFolderName.trim(), 'New Prompt', 'Enter your prompt here');
      await loadPrompts();
      setNewFolderName('');
      setShowAddFolder(false);
      // Expand the new folder
      setExpandedTabs(prev => new Set([...prev, newFolderName.trim()]));
    } catch (error) {
      console.error('Failed to create folder:', error);
    }
  };

  // Add new prompt to folder
  const handleAddPrompt = async (tabName: string) => {
    if (!newPromptName.trim() || !newPromptText.trim()) return;
    try {
      await promptsAPI.createTemplate(tabName, newPromptName.trim(), newPromptText.trim());
      await loadPrompts();
      setNewPromptName('');
      setNewPromptText('');
      setShowAddPrompt(null);
    } catch (error) {
      console.error('Failed to create prompt:', error);
    }
  };

  // Edit prompt
  const handleSavePrompt = async () => {
    if (!editingPrompt || !editingPrompt.name.trim()) return;
    try {
      await promptsAPI.updateTemplate(editingPrompt.id, {
        subtab_name: editingPrompt.name.trim(),
        prompt_text: editingPrompt.text.trim(),
      });
      await loadPrompts();
      setEditingPrompt(null);
    } catch (error) {
      console.error('Failed to update prompt:', error);
    }
  };

  // Delete prompt
  const handleDeletePrompt = async (promptId: number) => {
    if (!confirm('Are you sure you want to delete this prompt?')) return;
    try {
      await promptsAPI.deleteTemplate(promptId);
      await loadPrompts();
      setPromptMenu(null);
    } catch (error) {
      console.error('Failed to delete prompt:', error);
    }
  };

  // Move prompt to different folder
  const handleMovePrompt = async (promptId: number, newTabName: string) => {
    try {
      await promptsAPI.moveTemplate(promptId, newTabName);
      await loadPrompts();
      setShowMovePrompt(null);
      setPromptMenu(null);
    } catch (error) {
      console.error('Failed to move prompt:', error);
    }
  };

  // Rename folder
  const handleRenameFolder = async (oldName: string) => {
    if (!editFolderName.trim() || editFolderName === oldName) {
      setEditingFolder(null);
      return;
    }
    try {
      // Update all prompts in this folder to the new folder name
      const tab = promptTabs.find(t => t.tab_name === oldName);
      if (tab) {
        for (const subtab of tab.subtabs) {
          await promptsAPI.moveTemplate(subtab.id, editFolderName.trim());
        }
      }
      await loadPrompts();
      setEditingFolder(null);
      // Update expanded tabs
      setExpandedTabs(prev => {
        const newSet = new Set(prev);
        newSet.delete(oldName);
        newSet.add(editFolderName.trim());
        return newSet;
      });
    } catch (error) {
      console.error('Failed to rename folder:', error);
    }
  };

  // Delete folder
  const handleDeleteFolder = async (folderName: string) => {
    const tab = promptTabs.find(t => t.tab_name === folderName);
    const promptCount = tab?.subtabs.length || 0;
    if (!confirm(`Are you sure you want to delete "${folderName}" and its ${promptCount} prompt(s)?`)) return;
    try {
      // Delete all prompts in this folder
      if (tab) {
        for (const subtab of tab.subtabs) {
          await promptsAPI.deleteTemplate(subtab.id);
        }
      }
      await loadPrompts();
      setFolderMenu(null);
    } catch (error) {
      console.error('Failed to delete folder:', error);
    }
  };

  const toggleTab = (tabName: string) => {
    setExpandedTabs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(tabName)) {
        newSet.delete(tabName);
      } else {
        newSet.add(tabName);
      }
      return newSet;
    });
  };

  const startEditing = (session: ChatSession) => {
    setEditingSession(session.id);
    setEditTitle(session.title);
  };

  const saveTitle = (sessionId: number) => {
    if (editTitle.trim()) {
      onRenameSession(sessionId, editTitle.trim());
    }
    setEditingSession(null);
  };

  if (!isOpen) {
    return (
      <div className="w-12 h-full bg-dark-900 border-r border-dark-700 flex flex-col items-center py-4">
        <button
          onClick={onToggle}
          className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
        >
          <ChevronRight className="w-5 h-5 text-dark-400" />
        </button>
        <div className="mt-4 flex flex-col gap-2">
          <button
            onClick={onNewSession}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
            title="New Chat"
          >
            <Plus className="w-5 h-5 text-dark-400" />
          </button>
          <button
            onClick={() => { onToggle(); setActiveSection('chats'); }}
            className={cn(
              "p-2 rounded-lg transition-colors",
              activeSection === 'chats' ? "bg-accent-blue/20 text-accent-blue" : "hover:bg-dark-700 text-dark-400"
            )}
            title="Chats"
          >
            <MessageSquare className="w-5 h-5" />
          </button>
          <button
            onClick={() => { onToggle(); setActiveSection('prompts'); }}
            className={cn(
              "p-2 rounded-lg transition-colors",
              activeSection === 'prompts' ? "bg-accent-blue/20 text-accent-blue" : "hover:bg-dark-700 text-dark-400"
            )}
            title="Prompts"
          >
            <FileText className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={sidebarRef}
      className="h-full bg-dark-900 border-r border-dark-700 flex flex-col sidebar-transition relative"
      style={{ width: `${width}px`, minWidth: `${minWidth}px`, maxWidth: `${maxWidth}px` }}
    >
      {/* Resize Handle */}
      <div
        className={cn(
          "absolute right-0 top-0 bottom-0 w-1 cursor-col-resize group z-10",
          "hover:bg-accent-blue/50 transition-colors",
          isResizing && "bg-accent-blue"
        )}
        onMouseDown={handleMouseDown}
      >
        <div className={cn(
          "absolute right-0 top-1/2 -translate-y-1/2 -translate-x-1/2 p-0.5 rounded bg-dark-700 border border-dark-600",
          "opacity-0 group-hover:opacity-100 transition-opacity",
          isResizing && "opacity-100"
        )}>
          <GripVertical className="w-3 h-3 text-dark-400" />
        </div>
      </div>

      {/* Header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold gradient-text">Interview Assistant</h2>
          <button
            onClick={onToggle}
            className="p-1.5 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-dark-400" />
          </button>
        </div>
        
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-accent-blue hover:bg-accent-blue/90 text-white rounded-lg transition-colors btn-hover"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      {/* Section Tabs */}
      <div className="flex border-b border-dark-700">
        <button
          onClick={() => setActiveSection('chats')}
          className={cn(
            "flex-1 py-2.5 text-sm font-medium transition-colors",
            activeSection === 'chats' 
              ? "text-accent-blue border-b-2 border-accent-blue" 
              : "text-dark-400 hover:text-dark-200"
          )}
        >
          💬 Chats
        </button>
        <button
          onClick={() => setActiveSection('prompts')}
          className={cn(
            "flex-1 py-2.5 text-sm font-medium transition-colors",
            activeSection === 'prompts' 
              ? "text-accent-blue border-b-2 border-accent-blue" 
              : "text-dark-400 hover:text-dark-200"
          )}
        >
          📋 Prompts
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeSection === 'chats' ? (
          <div className="p-2">
            {sessions.length === 0 ? (
              <p className="text-dark-500 text-sm text-center py-8">
                No chats yet. Start a new conversation!
              </p>
            ) : (
              <div className="space-y-1">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className={cn(
                      "group relative flex items-center p-2.5 rounded-lg cursor-pointer transition-colors",
                      currentSessionId === session.id 
                        ? "bg-dark-700" 
                        : "hover:bg-dark-800"
                    )}
                    onClick={() => onSelectSession(session.id)}
                  >
                    <MessageSquare className="w-4 h-4 text-dark-400 mr-3 flex-shrink-0" />
                    
                    {editingSession === session.id ? (
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onBlur={() => saveTitle(session.id)}
                        onKeyDown={(e) => e.key === 'Enter' && saveTitle(session.id)}
                        className="flex-1 bg-dark-600 px-2 py-1 rounded text-sm focus:outline-none focus:ring-1 focus:ring-accent-blue"
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-dark-100 truncate">
                          {truncate(session.title, 24)}
                        </p>
                        <p className="text-xs text-dark-500">
                          {formatDate(session.updated_at)}
                        </p>
                      </div>
                    )}
                    
                    {/* Actions */}
                    <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 ml-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          startEditing(session);
                        }}
                        className="p-1 hover:bg-dark-600 rounded"
                      >
                        <Edit2 className="w-3.5 h-3.5 text-dark-400" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(session.id);
                        }}
                        className="p-1 hover:bg-dark-600 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5 text-accent-red" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="p-2">
            {/* Add Folder Button */}
            <button
              onClick={() => setShowAddFolder(true)}
              className="w-full flex items-center gap-2 p-2 mb-2 text-sm text-dark-400 hover:text-dark-200 hover:bg-dark-800 rounded-lg transition-colors border border-dashed border-dark-600"
            >
              <FolderPlus className="w-4 h-4" />
              <span>Add New Folder</span>
            </button>

            {/* Add Folder Form */}
            {showAddFolder && (
              <div className="mb-2 p-2 bg-dark-800 rounded-lg border border-dark-600">
                <input
                  type="text"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  placeholder="Folder name"
                  className="w-full px-2 py-1.5 bg-dark-700 border border-dark-600 rounded text-sm text-dark-100 focus:outline-none focus:ring-1 focus:ring-accent-blue"
                  autoFocus
                  onKeyDown={(e) => e.key === 'Enter' && handleAddFolder()}
                />
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={handleAddFolder}
                    className="flex-1 py-1 text-xs bg-accent-blue text-white rounded hover:bg-accent-blue/90"
                  >
                    Create
                  </button>
                  <button
                    onClick={() => { setShowAddFolder(false); setNewFolderName(''); }}
                    className="flex-1 py-1 text-xs bg-dark-700 text-dark-300 rounded hover:bg-dark-600"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {promptTabs.length === 0 ? (
              <p className="text-dark-500 text-sm text-center py-8">
                No prompts yet. Add a folder to get started!
              </p>
            ) : (
              <div className="space-y-1">
                {promptTabs.map((tab) => (
                  <div key={tab.tab_name}>
                    {/* Folder Header */}
                    <div className="group flex items-center">
                      {editingFolder === tab.tab_name ? (
                        <div className="flex-1 flex items-center gap-1 p-1">
                          <input
                            type="text"
                            value={editFolderName}
                            onChange={(e) => setEditFolderName(e.target.value)}
                            className="flex-1 px-2 py-1 bg-dark-700 border border-dark-600 rounded text-sm text-dark-100 focus:outline-none focus:ring-1 focus:ring-accent-blue"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleRenameFolder(tab.tab_name);
                              if (e.key === 'Escape') setEditingFolder(null);
                            }}
                            onBlur={() => handleRenameFolder(tab.tab_name)}
                          />
                        </div>
                      ) : (
                        <button
                          onClick={() => toggleTab(tab.tab_name)}
                          className="flex-1 flex items-center gap-2 p-2.5 hover:bg-dark-800 rounded-lg transition-colors"
                        >
                          {expandedTabs.has(tab.tab_name) ? (
                            <ChevronDown className="w-4 h-4 text-dark-400" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-dark-400" />
                          )}
                          <span className="text-sm font-medium text-dark-200">
                            📁 {tab.tab_name}
                          </span>
                          <span className="ml-auto text-xs text-dark-500 mr-1">
                            {tab.subtabs.length}
                          </span>
                        </button>
                      )}
                      
                      {/* Folder Menu */}
                      {editingFolder !== tab.tab_name && (
                        <div className="relative">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setFolderMenu(folderMenu === tab.tab_name ? null : tab.tab_name);
                            }}
                            className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-dark-700 rounded transition-all"
                          >
                            <MoreVertical className="w-4 h-4 text-dark-400" />
                          </button>
                          
                          {folderMenu === tab.tab_name && (
                            <div className="absolute right-0 top-full mt-1 w-32 bg-dark-800 border border-dark-600 rounded-lg shadow-lg z-20 py-1">
                              <button
                                onClick={() => {
                                  setEditingFolder(tab.tab_name);
                                  setEditFolderName(tab.tab_name);
                                  setFolderMenu(null);
                                }}
                                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-dark-300 hover:bg-dark-700"
                              >
                                <Edit2 className="w-3 h-3" /> Rename
                              </button>
                              <button
                                onClick={() => {
                                  setShowAddPrompt(tab.tab_name);
                                  setFolderMenu(null);
                                }}
                                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-dark-300 hover:bg-dark-700"
                              >
                                <Plus className="w-3 h-3" /> Add Prompt
                              </button>
                              <button
                                onClick={() => handleDeleteFolder(tab.tab_name)}
                                className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-accent-red hover:bg-dark-700"
                              >
                                <Trash2 className="w-3 h-3" /> Delete
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    
                    {/* Folder Contents */}
                    {expandedTabs.has(tab.tab_name) && (
                      <div className="ml-4 mt-1 space-y-0.5 border-l border-dark-700 pl-2">
                        {/* Add Prompt Form */}
                        {showAddPrompt === tab.tab_name && (
                          <div className="p-2 bg-dark-800 rounded-lg border border-dark-600 mb-1">
                            <input
                              type="text"
                              value={newPromptName}
                              onChange={(e) => setNewPromptName(e.target.value)}
                              placeholder="Prompt name"
                              className="w-full px-2 py-1.5 mb-2 bg-dark-700 border border-dark-600 rounded text-sm text-dark-100 focus:outline-none focus:ring-1 focus:ring-accent-blue"
                              autoFocus
                            />
                            <textarea
                              value={newPromptText}
                              onChange={(e) => setNewPromptText(e.target.value)}
                              placeholder="Prompt text..."
                              className="w-full px-2 py-1.5 bg-dark-700 border border-dark-600 rounded text-sm text-dark-100 focus:outline-none focus:ring-1 focus:ring-accent-blue resize-none"
                              rows={3}
                            />
                            <div className="flex gap-2 mt-2">
                              <button
                                onClick={() => handleAddPrompt(tab.tab_name)}
                                className="flex-1 py-1 text-xs bg-accent-blue text-white rounded hover:bg-accent-blue/90"
                              >
                                Add
                              </button>
                              <button
                                onClick={() => { setShowAddPrompt(null); setNewPromptName(''); setNewPromptText(''); }}
                                className="flex-1 py-1 text-xs bg-dark-700 text-dark-300 rounded hover:bg-dark-600"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}

                        {/* Prompt Items */}
                        {tab.subtabs.map((subtab) => (
                          <div key={subtab.id} className="group relative">
                            {editingPrompt?.id === subtab.id ? (
                              <div className="p-2 bg-dark-800 rounded-lg border border-dark-600">
                                <input
                                  type="text"
                                  value={editingPrompt.name}
                                  onChange={(e) => setEditingPrompt({...editingPrompt, name: e.target.value})}
                                  className="w-full px-2 py-1.5 mb-2 bg-dark-700 border border-dark-600 rounded text-sm text-dark-100 focus:outline-none focus:ring-1 focus:ring-accent-blue"
                                  autoFocus
                                />
                                <textarea
                                  value={editingPrompt.text}
                                  onChange={(e) => setEditingPrompt({...editingPrompt, text: e.target.value})}
                                  className="w-full px-2 py-1.5 bg-dark-700 border border-dark-600 rounded text-sm text-dark-100 focus:outline-none focus:ring-1 focus:ring-accent-blue resize-none"
                                  rows={3}
                                />
                                <div className="flex gap-2 mt-2">
                                  <button
                                    onClick={handleSavePrompt}
                                    className="flex-1 py-1 text-xs bg-accent-green text-white rounded hover:bg-accent-green/90"
                                  >
                                    Save
                                  </button>
                                  <button
                                    onClick={() => setEditingPrompt(null)}
                                    className="flex-1 py-1 text-xs bg-dark-700 text-dark-300 rounded hover:bg-dark-600"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="flex items-center">
                                <button
                                  onClick={() => onSelectPrompt(subtab.prompt_text)}
                                  className="flex-1 text-left p-2 text-sm text-dark-300 hover:text-dark-100 hover:bg-dark-800 rounded-lg transition-colors truncate"
                                  title={subtab.prompt_text}
                                >
                                  {subtab.subtab_name}
                                </button>
                                
                                {/* Prompt Menu */}
                                <div className="relative">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setPromptMenu(promptMenu?.id === subtab.id ? null : {id: subtab.id, tabName: tab.tab_name});
                                    }}
                                    className="p-1 opacity-0 group-hover:opacity-100 hover:bg-dark-700 rounded transition-all"
                                  >
                                    <MoreVertical className="w-3.5 h-3.5 text-dark-400" />
                                  </button>
                                  
                                  {promptMenu?.id === subtab.id && (
                                    <div className="absolute right-0 top-full mt-1 w-32 bg-dark-800 border border-dark-600 rounded-lg shadow-lg z-20 py-1">
                                      <button
                                        onClick={() => {
                                          onSelectPrompt(subtab.prompt_text);
                                          setPromptMenu(null);
                                        }}
                                        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-dark-300 hover:bg-dark-700"
                                      >
                                        <Check className="w-3 h-3" /> Use
                                      </button>
                                      <button
                                        onClick={() => {
                                          setEditingPrompt({id: subtab.id, name: subtab.subtab_name, text: subtab.prompt_text});
                                          setPromptMenu(null);
                                        }}
                                        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-dark-300 hover:bg-dark-700"
                                      >
                                        <Edit2 className="w-3 h-3" /> Edit
                                      </button>
                                      <button
                                        onClick={() => {
                                          navigator.clipboard.writeText(subtab.prompt_text);
                                          setPromptMenu(null);
                                        }}
                                        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-dark-300 hover:bg-dark-700"
                                      >
                                        <Copy className="w-3 h-3" /> Copy
                                      </button>
                                      <button
                                        onClick={() => {
                                          setShowMovePrompt({id: subtab.id, currentTab: tab.tab_name});
                                          setPromptMenu(null);
                                        }}
                                        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-dark-300 hover:bg-dark-700"
                                      >
                                        <Move className="w-3 h-3" /> Move
                                      </button>
                                      <button
                                        onClick={() => handleDeletePrompt(subtab.id)}
                                        className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-accent-red hover:bg-dark-700"
                                      >
                                        <Trash2 className="w-3 h-3" /> Delete
                                      </button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}

                        {/* Add prompt button at bottom of folder */}
                        {showAddPrompt !== tab.tab_name && (
                          <button
                            onClick={() => setShowAddPrompt(tab.tab_name)}
                            className="w-full flex items-center gap-2 p-2 text-xs text-dark-500 hover:text-dark-300 hover:bg-dark-800 rounded-lg transition-colors"
                          >
                            <Plus className="w-3 h-3" /> Add prompt
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Move Prompt Modal */}
            {showMovePrompt && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                <div className="bg-dark-800 rounded-lg border border-dark-600 p-4 w-64 shadow-xl">
                  <h3 className="text-sm font-semibold text-dark-200 mb-3">Move to folder</h3>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {promptTabs.filter(t => t.tab_name !== showMovePrompt.currentTab).map(tab => (
                      <button
                        key={tab.tab_name}
                        onClick={() => handleMovePrompt(showMovePrompt.id, tab.tab_name)}
                        className="w-full text-left p-2 text-sm text-dark-300 hover:bg-dark-700 rounded"
                      >
                        📁 {tab.tab_name}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setShowMovePrompt(null)}
                    className="w-full mt-3 py-1.5 text-xs bg-dark-700 text-dark-300 rounded hover:bg-dark-600"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-dark-700">
        <div className="flex items-center justify-between text-xs text-dark-500">
          <span>{sessions.length} chats</span>
          <button className="hover:text-dark-300 transition-colors">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}



