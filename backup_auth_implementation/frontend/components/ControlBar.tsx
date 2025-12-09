'use client';

import { useState } from 'react';
import {
  Upload,
  Zap,
  ZapOff,
  Settings2,
  BarChart3,
  Bookmark,
  Plus,
  Minus,
  RefreshCw,
  Rocket,
  ChevronDown,
  Pin,
  PinOff,
  Keyboard,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ModelType, AnswerMode } from '@/types';
import UserMenu from './UserMenu';

interface ControlBarProps {
  model: ModelType;
  answerMode: AnswerMode;
  optimizationMode: boolean;
  fontSize: number;
  apiConnected: boolean;
  onModelChange: (model: ModelType) => void;
  onAnswerModeChange: (mode: AnswerMode) => void;
  onOptimizationToggle: () => void;
  onFontSizeChange: (delta: number) => void;
  onUploadDocument: () => void;
  onShowDiagnostics: () => void;
  onShowBookmarks: () => void;
  onQuickSetup: () => void;
  onNewChat: () => void;
  onShowHotkeys?: () => void;
}

const MODEL_OPTIONS: { value: ModelType; label: string; icon: string }[] = [
  { value: 'gpt-4o', label: 'GPT-4o', icon: '🧠' },
  { value: 'gpt-4o-mini', label: 'Mini', icon: '⚡' },
  { value: 'gpt-4-turbo', label: 'Turbo', icon: '🚀' },
];

const ANSWER_MODE_OPTIONS: { value: AnswerMode; label: string; icon: string }[] = [
  { value: 'default', label: 'Default', icon: '🔘' },
  { value: 'quick', label: 'Quick', icon: '⚡' },
  { value: 'detailed', label: 'Detailed', icon: '📝' },
  { value: 'code', label: 'Code', icon: '💻' },
];

export default function ControlBar({
  model,
  answerMode,
  optimizationMode,
  fontSize,
  apiConnected,
  onModelChange,
  onAnswerModeChange,
  onOptimizationToggle,
  onFontSizeChange,
  onUploadDocument,
  onShowDiagnostics,
  onShowBookmarks,
  onQuickSetup,
  onNewChat,
  onShowHotkeys,
}: ControlBarProps) {
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const [showModeDropdown, setShowModeDropdown] = useState(false);

  const currentModel = MODEL_OPTIONS.find((m) => m.value === model);
  const currentMode = ANSWER_MODE_OPTIONS.find((m) => m.value === answerMode);

  return (
    <div className="border-b border-dark-700 bg-dark-900/80 backdrop-blur-sm">
      {/* Top Row - Status and Actions */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-dark-800">
        {/* Left - Status */}
        <div className="flex items-center gap-3">
          <div className={cn(
            "flex items-center gap-1.5 px-2 py-1 rounded-full text-xs",
            apiConnected ? "bg-accent-green/10 text-accent-green" : "bg-accent-red/10 text-accent-red"
          )}>
            <div className={cn(
              "w-2 h-2 rounded-full",
              apiConnected ? "bg-accent-green" : "bg-accent-red"
            )} />
            {apiConnected ? 'Connected' : 'Offline'}
          </div>
        </div>

        {/* Right - Quick Actions & User */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={onNewChat}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-accent-blue hover:bg-accent-blue/90 text-white rounded-lg transition-colors"
            >
            <RefreshCw className="w-3.5 h-3.5" />
            New Chat
          </button>
          <button
            onClick={onUploadDocument}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-lg transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            Resume/JD
          </button>
          </div>
          
          {/* User Menu */}
          <UserMenu />
        </div>
      </div>

      {/* Bottom Row - Settings */}
      <div className="flex items-center justify-between px-4 py-2">
        {/* Left - Model & Mode */}
        <div className="flex items-center gap-2">
          {/* Model Selector */}
          <div className="relative">
            <button
              onClick={() => setShowModelDropdown(!showModelDropdown)}
              onBlur={() => setTimeout(() => setShowModelDropdown(false), 200)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-dark-800 hover:bg-dark-700 rounded-lg text-sm transition-colors"
            >
              <span>{currentModel?.icon}</span>
              <span className="text-dark-200">{currentModel?.label}</span>
              <ChevronDown className="w-3.5 h-3.5 text-dark-400" />
            </button>
            
            {showModelDropdown && (
              <div className="absolute top-full left-0 mt-1 w-40 bg-dark-800 border border-dark-600 rounded-lg shadow-xl z-50">
                {MODEL_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      onModelChange(option.value);
                      setShowModelDropdown(false);
                    }}
                    className={cn(
                      "w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-dark-700 transition-colors first:rounded-t-lg last:rounded-b-lg",
                      model === option.value ? "text-accent-blue" : "text-dark-200"
                    )}
                  >
                    <span>{option.icon}</span>
                    <span>{option.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Answer Mode Selector */}
          <div className="relative">
            <button
              onClick={() => setShowModeDropdown(!showModeDropdown)}
              onBlur={() => setTimeout(() => setShowModeDropdown(false), 200)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-dark-800 hover:bg-dark-700 rounded-lg text-sm transition-colors"
            >
              <span>{currentMode?.icon}</span>
              <span className="text-dark-200">{currentMode?.label}</span>
              <ChevronDown className="w-3.5 h-3.5 text-dark-400" />
            </button>
            
            {showModeDropdown && (
              <div className="absolute top-full left-0 mt-1 w-40 bg-dark-800 border border-dark-600 rounded-lg shadow-xl z-50">
                {ANSWER_MODE_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      onAnswerModeChange(option.value);
                      setShowModeDropdown(false);
                    }}
                    className={cn(
                      "w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-dark-700 transition-colors first:rounded-t-lg last:rounded-b-lg",
                      answerMode === option.value ? "text-accent-blue" : "text-dark-200"
                    )}
                  >
                    <span>{option.icon}</span>
                    <span>{option.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Optimization Toggle */}
          <button
            onClick={onOptimizationToggle}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors",
              optimizationMode 
                ? "bg-accent-amber/20 text-accent-amber" 
                : "bg-dark-800 hover:bg-dark-700 text-dark-400"
            )}
            title={optimizationMode ? "Fast Mode ON" : "Fast Mode OFF"}
          >
            {optimizationMode ? (
              <>
                <Zap className="w-3.5 h-3.5" />
                Fast
              </>
            ) : (
              <>
                <ZapOff className="w-3.5 h-3.5" />
                Full
              </>
            )}
          </button>
        </div>

        {/* Right - Tools */}
        <div className="flex items-center gap-1">
          {/* Quick Setup */}
          <button
            onClick={onQuickSetup}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors text-dark-400 hover:text-dark-200"
            title="Quick Setup"
          >
            <Rocket className="w-4 h-4" />
          </button>

          {/* Bookmarks */}
          <button
            onClick={onShowBookmarks}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors text-dark-400 hover:text-dark-200"
            title="Bookmarks"
          >
            <Bookmark className="w-4 h-4" />
          </button>

          {/* Diagnostics */}
          <button
            onClick={onShowDiagnostics}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors text-dark-400 hover:text-dark-200"
            title="Performance Diagnostics"
          >
            <BarChart3 className="w-4 h-4" />
          </button>

          {/* Keyboard Shortcuts */}
          {onShowHotkeys && (
            <button
              onClick={onShowHotkeys}
              className="p-2 hover:bg-dark-700 rounded-lg transition-colors text-dark-400 hover:text-dark-200"
              title="Keyboard Shortcuts (?)"
            >
              <Keyboard className="w-4 h-4" />
            </button>
          )}

          {/* Divider */}
          <div className="w-px h-5 bg-dark-700 mx-1" />

          {/* Font Size Controls */}
          <button
            onClick={() => onFontSizeChange(-1)}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors text-dark-400 hover:text-dark-200"
            title="Decrease font size"
          >
            <Minus className="w-4 h-4" />
          </button>
          <span className="text-xs text-dark-500 w-8 text-center">{fontSize}px</span>
          <button
            onClick={() => onFontSizeChange(1)}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors text-dark-400 hover:text-dark-200"
            title="Increase font size"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

