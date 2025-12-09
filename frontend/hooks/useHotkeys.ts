'use client';

import { useEffect, useCallback, useRef } from 'react';

type HotkeyHandler = () => void;

interface HotkeyConfig {
  // Recording controls
  onStartRecording?: HotkeyHandler;
  onStopRecording?: HotkeyHandler;
  onToggleRecording?: HotkeyHandler;
  onListenExternal?: HotkeyHandler; // 5+6: Start/stop recording with external mic
  onListenInternal?: HotkeyHandler; // Start/stop recording with BlackHole
  
  // Screenshot
  onCaptureScreenshot?: HotkeyHandler;
  
  // Navigation
  onFocusInput?: HotkeyHandler;
  onUploadResume?: HotkeyHandler;
  onQuickSetup?: HotkeyHandler;
  onNewChat?: HotkeyHandler;
  
  // Chat scroll
  onScrollToBottom?: HotkeyHandler; // PageDown - scroll to end of chat
  onScrollToTop?: HotkeyHandler;    // PageUp - scroll to top of chat
  
  // Font size
  onIncreaseFontSize?: HotkeyHandler;
  onDecreaseFontSize?: HotkeyHandler;
  
  // Bookmarks
  onAddBookmark?: HotkeyHandler;
  onToggleBookmarks?: HotkeyHandler;
  
  // Model & Settings
  onToggleModel?: HotkeyHandler;
  onToggleOptimization?: HotkeyHandler;
  onToggleDiagnostics?: HotkeyHandler;
  
  // Other
  onToggleSidebar?: HotkeyHandler;
  onCopyLastResponse?: HotkeyHandler;
  onClearChat?: HotkeyHandler;
  
  // UI Layout
  onSaveLayout?: HotkeyHandler; // F2 - Save UI layout
}

// Track currently pressed keys for combo detection
const pressedKeys = new Set<string>();

export function useHotkeys(config: HotkeyConfig) {
  const configRef = useRef(config);
  configRef.current = config;

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const key = event.key.toLowerCase();
    const isCmd = event.metaKey || event.ctrlKey;
    const isShift = event.shiftKey;
    const isAlt = event.altKey;
    
    // Add to pressed keys for combo detection
    pressedKeys.add(key);
    
    // Don't trigger hotkeys when typing in input fields (unless it's a specific combo)
    const isTyping = ['INPUT', 'TEXTAREA'].includes((event.target as HTMLElement).tagName);
    
    // =========================================
    // RECORDING CONTROLS
    // =========================================
    // NOTE: Recording hotkeys (` and ~) are now handled directly by ChatInput component
    // to ensure proper access to recording state and auto-send functionality
    
    // =========================================
    // SCREENSHOT
    // =========================================
    
    // ! (Exclamation/Shift+1) - Capture Screenshot
    if (key === '!' || (key === '1' && isShift && !isTyping)) {
      event.preventDefault();
      console.log('📸 Hotkey: Capture Screenshot');
      configRef.current.onCaptureScreenshot?.();
      return;
    }
    
    // =========================================
    // QUICK ACTIONS (Number Combos)
    // =========================================
    
    // 1 + 2 - Focus Chat Input
    if (pressedKeys.has('1') && pressedKeys.has('2') && !isTyping) {
      event.preventDefault();
      console.log('⌨️ Hotkey 1+2: Focus Chat Input');
      configRef.current.onFocusInput?.();
      return;
    }
    
    // 2 + 3 - Upload Resume/JD
    if (pressedKeys.has('2') && pressedKeys.has('3') && !isTyping) {
      event.preventDefault();
      console.log('📁 Hotkey 2+3: Upload Resume/JD');
      configRef.current.onUploadResume?.();
      return;
    }
    
    // 3 + 4 - Toggle Optimization Mode
    if (pressedKeys.has('3') && pressedKeys.has('4') && !isTyping) {
      event.preventDefault();
      console.log('⚡ Hotkey 3+4: Toggle Optimization');
      configRef.current.onToggleOptimization?.();
      return;
    }
    
    // 5 + 6 - Listen with External Mic (toggle recording with microphone)
    if (pressedKeys.has('5') && pressedKeys.has('6') && !isTyping) {
      event.preventDefault();
      console.log('🎧 Hotkey 5+6: Listen with External Mic');
      configRef.current.onListenExternal?.();
      return;
    }
    
    // 4 + 5 - Listen with Internal Audio (BlackHole)
    if (pressedKeys.has('4') && pressedKeys.has('5') && !isTyping) {
      event.preventDefault();
      console.log('🔊 Hotkey 4+5: Listen with Internal Audio (BlackHole)');
      configRef.current.onListenInternal?.();
      return;
    }
    
    // =========================================
    // COMMAND/CTRL SHORTCUTS
    // =========================================
    
    if (isCmd) {
      // Cmd/Ctrl + Shift + S - Quick Setup
      if (isShift && key === 's') {
        event.preventDefault();
        console.log('🚀 Hotkey Cmd+Shift+S: Quick Setup');
        configRef.current.onQuickSetup?.();
        return;
      }
      
      // Cmd/Ctrl + B - Add Bookmark
      if (key === 'b' && !isShift) {
        event.preventDefault();
        console.log('🔖 Hotkey Cmd+B: Add Bookmark');
        configRef.current.onAddBookmark?.();
        return;
      }
      
      // Cmd/Ctrl + P - Toggle Sidebar (Pin)
      if (key === 'p' && !isShift) {
        event.preventDefault();
        console.log('📌 Hotkey Cmd+P: Toggle Sidebar');
        configRef.current.onToggleSidebar?.();
        return;
      }
      
      // Cmd/Ctrl + = or + - Increase Font Size
      if (key === '=' || key === '+') {
        event.preventDefault();
        console.log('🔎 Hotkey Cmd+=: Increase Font');
        configRef.current.onIncreaseFontSize?.();
        return;
      }
      
      // Cmd/Ctrl + - - Decrease Font Size
      if (key === '-') {
        event.preventDefault();
        console.log('🔍 Hotkey Cmd+-: Decrease Font');
        configRef.current.onDecreaseFontSize?.();
        return;
      }
      
      // Cmd/Ctrl + N - New Chat
      if (key === 'n' && !isShift) {
        event.preventDefault();
        console.log('💬 Hotkey Cmd+N: New Chat');
        configRef.current.onNewChat?.();
        return;
      }
      
      // Cmd/Ctrl + M - Toggle Model
      if (key === 'm' && !isShift) {
        event.preventDefault();
        console.log('🧠 Hotkey Cmd+M: Toggle Model');
        configRef.current.onToggleModel?.();
        return;
      }
      
      // Cmd/Ctrl + D - Toggle Diagnostics
      if (key === 'd' && !isShift) {
        event.preventDefault();
        console.log('📊 Hotkey Cmd+D: Diagnostics');
        configRef.current.onToggleDiagnostics?.();
        return;
      }
      
      // Cmd/Ctrl + Shift + C - Copy Last Response
      if (isShift && key === 'c' && !isTyping) {
        event.preventDefault();
        console.log('📋 Hotkey Cmd+Shift+C: Copy Last Response');
        configRef.current.onCopyLastResponse?.();
        return;
      }
      
      // Cmd/Ctrl + Shift + Delete/Backspace - Clear Chat
      if (isShift && (key === 'delete' || key === 'backspace') && !isTyping) {
        event.preventDefault();
        console.log('🗑️ Hotkey Cmd+Shift+Del: Clear Chat');
        configRef.current.onClearChat?.();
        return;
      }
    }
    
    // =========================================
    // FUNCTION KEYS
    // =========================================
    
    // F2 - Save UI Layout
    if (key === 'f2') {
      event.preventDefault();
      console.log('💾 Hotkey F2: Save UI Layout');
      configRef.current.onSaveLayout?.();
      return;
    }
    
    // F4 - Add Bookmark (alternative)
    if (key === 'f4') {
      event.preventDefault();
      console.log('🔖 Hotkey F4: Add Bookmark');
      configRef.current.onAddBookmark?.();
      return;
    }
    
    // F5 - Toggle Bookmarks Panel
    if (key === 'f5') {
      event.preventDefault();
      console.log('📚 Hotkey F5: Toggle Bookmarks');
      configRef.current.onToggleBookmarks?.();
      return;
    }
    
    // F6 - Quick Setup (alternative)
    if (key === 'f6') {
      event.preventDefault();
      console.log('🚀 Hotkey F6: Quick Setup');
      configRef.current.onQuickSetup?.();
      return;
    }
    
    // F7 - Toggle Optimization
    if (key === 'f7') {
      event.preventDefault();
      console.log('⚡ Hotkey F7: Toggle Optimization');
      configRef.current.onToggleOptimization?.();
      return;
    }
    
    // F8 - New Chat (alternative)
    if (key === 'f8') {
      event.preventDefault();
      console.log('💬 Hotkey F8: New Chat');
      configRef.current.onNewChat?.();
      return;
    }
    
    // Escape - Focus input / Close modals
    if (key === 'escape') {
      console.log('⎋ Hotkey Escape: Focus Input');
      configRef.current.onFocusInput?.();
      return;
    }
    
    // =========================================
    // CHAT SCROLL NAVIGATION
    // =========================================
    
    // PageDown - Scroll to bottom of chat
    if (key === 'pagedown') {
      event.preventDefault();
      console.log('⬇️ Hotkey PageDown: Scroll to Bottom');
      configRef.current.onScrollToBottom?.();
      return;
    }
    
    // PageUp - Scroll to top of chat
    if (key === 'pageup') {
      event.preventDefault();
      console.log('⬆️ Hotkey PageUp: Scroll to Top');
      configRef.current.onScrollToTop?.();
      return;
    }
    
    // End - Also scroll to bottom (alternative)
    if (key === 'end' && !isTyping) {
      event.preventDefault();
      console.log('⬇️ Hotkey End: Scroll to Bottom');
      configRef.current.onScrollToBottom?.();
      return;
    }
    
    // Home - Also scroll to top (alternative)
    if (key === 'home' && !isTyping) {
      event.preventDefault();
      console.log('⬆️ Hotkey Home: Scroll to Top');
      configRef.current.onScrollToTop?.();
      return;
    }
    
  }, []);

  const handleKeyUp = useCallback((event: KeyboardEvent) => {
    const key = event.key.toLowerCase();
    pressedKeys.delete(key);
  }, []);

  // Clear pressed keys on window blur (prevents stuck keys)
  const handleBlur = useCallback(() => {
    pressedKeys.clear();
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('blur', handleBlur);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('blur', handleBlur);
      pressedKeys.clear();
    };
  }, [handleKeyDown, handleKeyUp, handleBlur]);
}

// Helper component to display hotkey hints
export const HOTKEY_HINTS = {
  recording: '` to start/stop recording',
  forceStop: '~ to force stop',
  screenshot: 'Shift+1 to capture screenshot',
  focusInput: '1+2 to focus input',
  uploadResume: '2+3 to upload resume',
  toggleOptimization: '3+4 to toggle fast mode',
  listenInternal: '4+5 to record with BlackHole',
  listenExternal: '5+6 to record with external mic',
  quickSetup: 'Cmd+Shift+S or F6',
  bookmark: 'Cmd+B or F4',
  newChat: 'Cmd+N or F8',
  toggleModel: 'Cmd+M',
  diagnostics: 'Cmd+D',
  fontIncrease: 'Cmd+=',
  fontDecrease: 'Cmd+-',
  toggleSidebar: 'Cmd+P',
  copyResponse: 'Cmd+Shift+C',
  bookmarks: 'F5',
  scrollToBottom: 'PageDown or End',
  scrollToTop: 'PageUp or Home',
  saveLayout: 'F2 to save UI layout',
};

