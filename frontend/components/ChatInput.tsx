'use client';

import { useState, useRef, useEffect, useCallback, KeyboardEvent, ClipboardEvent, useImperativeHandle, forwardRef } from 'react';
import { 
  Send, 
  Mic, 
  MicOff, 
  Image as ImageIcon, 
  X, 
  Upload,
  Paperclip,
  StopCircle,
  Volume2,
  Headphones,
  ChevronDown,
  Settings2,
  GripHorizontal
} from 'lucide-react';
import { cn, compressImage, getClipboardImage } from '@/lib/utils';
import { useAudioRecorder, AudioInputMode, AudioDevice } from '@/hooks/useAudioRecorder';

interface ChatInputProps {
  onSend: (message: string, images?: string[]) => void;
  onStop?: () => void;
  isStreaming: boolean;
  pendingImages: string[];
  onAddImage: (image: string) => void;
  onRemoveImage: (index: number) => void;
  onClearImages: () => void;
  disabled?: boolean;
  autoSendOnRecordStop?: boolean; // Auto-send transcription to GPT when recording stops
  onRecordingStateChange?: (isRecording: boolean) => void;
  listenExternalTrigger?: number; // Increment to trigger external mic recording (5+6 hotkey)
  listenInternalTrigger?: number; // Increment to trigger internal (BlackHole) recording (4+5 hotkey)
  inputHeight?: number; // Controlled height for the input area
  onInputHeightChange?: (height: number) => void; // Callback when height changes
  minInputHeight?: number;
  maxInputHeight?: number;
}

export default function ChatInput({
  onSend,
  onStop,
  isStreaming,
  pendingImages,
  onAddImage,
  onRemoveImage,
  onClearImages,
  disabled = false,
  autoSendOnRecordStop = true, // Default: auto-send to GPT
  onRecordingStateChange,
  listenExternalTrigger,
  listenInternalTrigger,
  inputHeight = 120,
  onInputHeightChange,
  minInputHeight = 80,
  maxInputHeight = 400,
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [showDeviceMenu, setShowDeviceMenu] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false); // Processing transcription
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Session management for quick transitions
  const sessionIdRef = useRef<number>(0); // Unique ID for each recording session
  const activeSessionRef = useRef<number>(0); // Which session should we process

  // Handle resize drag
  const handleResizeMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const newHeight = containerRect.bottom - e.clientY;
      const clampedHeight = Math.min(maxInputHeight, Math.max(minInputHeight, newHeight));
      onInputHeightChange?.(clampedHeight);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, minInputHeight, maxInputHeight, onInputHeightChange]);
  
  const { 
    isRecording, 
    audioLevel, 
    liveText, 
    inputMode,
    currentDevice,
    availableDevices,
    toggleRecording, 
    stopRecording,
    cancelRecording,
    toggleInputMode,
    setInputMode,
    selectDevice,
    startRecordingWithMode,
    isStreamReady,
    warmUpStream
  } = useAudioRecorder();
  
  // Warm up stream on mount for instant recording
  useEffect(() => {
    const timer = setTimeout(() => {
      warmUpStream();
    }, 500);
    return () => clearTimeout(timer);
  }, [warmUpStream]);

  // Notify parent of recording state changes
  useEffect(() => {
    onRecordingStateChange?.(isRecording);
  }, [isRecording, onRecordingStateChange]);

  // Handle 5+6 hotkey: Listen with External Mic
  useEffect(() => {
    if (listenExternalTrigger && listenExternalTrigger > 0) {
      console.log('🎧 5+6 Hotkey triggered: External Mic Recording');
      if (isRecording) {
        // If already recording, stop and process
        handleRecordToggle();
      } else {
        // Set to external mode and start recording
        setInputMode('external');
        setTimeout(() => {
          handleRecordToggleRef.current();
        }, 100);
      }
    }
  }, [listenExternalTrigger]);

  // Handle 4+5 hotkey: Listen with Internal Audio (BlackHole)
  useEffect(() => {
    if (listenInternalTrigger && listenInternalTrigger > 0) {
      console.log('🔊 4+5 Hotkey triggered: Internal Audio Recording (BlackHole)');
      if (isRecording) {
        // If already recording, stop and process
        handleRecordToggle();
      } else {
        // Set to internal mode and start recording
        setInputMode('internal');
        setTimeout(() => {
          handleRecordToggleRef.current();
        }, 100);
      }
    }
  }, [listenInternalTrigger]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  // Focus textarea on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage && pendingImages.length === 0) return;
    
    onSend(trimmedMessage, pendingImages.length > 0 ? pendingImages : undefined);
    setMessage('');
    onClearImages();
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePaste = async (e: ClipboardEvent<HTMLTextAreaElement>) => {
    // Check for image in clipboard
    const items = e.clipboardData?.items;
    if (items) {
      const itemsArray = Array.from(items);
      for (const item of itemsArray) {
        if (item.type.startsWith('image/')) {
          e.preventDefault();
          const file = item.getAsFile();
          if (file) {
            try {
              const compressed = await compressImage(file);
              onAddImage(compressed);
            } catch (error) {
              console.error('Failed to process pasted image:', error);
            }
          }
          return;
        }
      }
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const filesArray = Array.from(files);
    for (const file of filesArray) {
      if (file.type.startsWith('image/')) {
        try {
          const compressed = await compressImage(file);
          onAddImage(compressed);
        } catch (error) {
          console.error('Failed to process image:', error);
        }
      }
    }

    // Reset input
    e.target.value = '';
  };

  const handleRecordToggle = async () => {
    // ALWAYS stop GPT stream if running when pressing backtick
    if (isStreaming && onStop) {
      console.log('⚡ Stopping GPT stream');
      onStop();
    }
    
    if (isRecording) {
      // === STOP RECORDING & SEND ===
      const mySession = sessionIdRef.current;
      activeSessionRef.current = mySession;
      
      console.log(`🛑 [Session ${mySession}] Stopping recording...`);
      setIsProcessing(true);
      
      // Stop recording immediately (non-blocking for UI)
      stopRecording().then(async (transcription) => {
        // Check if this session is still the active one
        if (activeSessionRef.current !== mySession) {
          console.log(`⚡ [Session ${mySession}] Discarded - newer session active`);
          return;
        }
        
        if (transcription && transcription.trim()) {
          const cleanText = transcription.trim()
            .replace(/\(transcribing\.\.\.\)/g, '')
            .replace(/⚡.*?\.\.\./g, '')
            .replace(/🎧.*?\.\.\./g, '')
            .trim();
          
          // Double-check still active session before sending
          if (activeSessionRef.current !== mySession) {
            console.log(`⚡ [Session ${mySession}] Discarded before send`);
            setIsProcessing(false);
            return;
          }
          
          if (cleanText && autoSendOnRecordStop) {
            console.log(`🚀 [Session ${mySession}] Sending: "${cleanText.slice(0, 40)}..."`);
            onSend(cleanText, pendingImages.length > 0 ? pendingImages : undefined);
            onClearImages();
            setMessage('');
          } else if (cleanText) {
            setMessage(prev => prev + (prev ? ' ' : '') + cleanText);
          }
        }
        setIsProcessing(false);
      }).catch((error) => {
        console.error(`❌ [Session ${mySession}] Error:`, error);
        setIsProcessing(false);
      });
      
    } else {
      // === START NEW RECORDING ===
      // Increment session ID - this invalidates any pending transcriptions
      sessionIdRef.current += 1;
      activeSessionRef.current = sessionIdRef.current;
      const mySession = sessionIdRef.current;
      
      console.log(`🎤 [Session ${mySession}] Starting new recording...`);
      
      // Cancel any processing state from previous session
      setIsProcessing(false);
      
      // If there's an old recording somehow still active, cancel it
      if (isRecording) {
        cancelRecording();
      }
      
      // Start new recording
      try {
        await toggleRecording();
        console.log(`✅ [Session ${mySession}] Recording started`);
      } catch (error) {
        console.error(`❌ [Session ${mySession}] Failed to start:`, error);
      }
    }
  };

  // Store handleRecordToggle in a ref for the effect to use
  const handleRecordToggleRef = useRef(handleRecordToggle);
  handleRecordToggleRef.current = handleRecordToggle;

  // Debounce ref for rapid key presses
  const lastKeyPressRef = useRef<number>(0);
  const keyPressDebounceMs = 150; // Minimum time between key presses
  
  // Global hotkey listener for recording (backtick key)
  useEffect(() => {
    const handleGlobalKeyDown = (e: globalThis.KeyboardEvent) => {
      // Backtick (`) to toggle recording
      if (e.key === '`' || e.key === '~') {
        e.preventDefault();
        e.stopPropagation();
        
        const now = Date.now();
        const timeSinceLast = now - lastKeyPressRef.current;
        
        // Debounce rapid presses but still allow them
        if (timeSinceLast < keyPressDebounceMs) {
          console.log(`⏳ Key debounced (${timeSinceLast}ms < ${keyPressDebounceMs}ms)`);
          return;
        }
        
        lastKeyPressRef.current = now;
        console.log(`🎤 Hotkey ${e.key} pressed`);
        handleRecordToggleRef.current();
        return;
      }
    };

    // Add listener to window for global hotkeys (capture phase)
    window.addEventListener('keydown', handleGlobalKeyDown, true);
    
    return () => {
      window.removeEventListener('keydown', handleGlobalKeyDown, true);
    };
  }, []);

  // Calculate textarea max height based on input area height
  const textareaMaxHeight = Math.max(48, inputHeight - 100); // Leave room for buttons and hints

  return (
    <div 
      ref={containerRef}
      className="border-t border-dark-700 bg-dark-900 relative flex flex-col"
      style={{ minHeight: `${inputHeight}px` }}
    >
      {/* Resize Handle */}
      <div
        className={cn(
          "absolute top-0 left-0 right-0 h-2 cursor-row-resize group z-10 flex items-center justify-center",
          "hover:bg-accent-blue/20 transition-colors",
          isResizing && "bg-accent-blue/30"
        )}
        onMouseDown={handleResizeMouseDown}
      >
        <div className={cn(
          "p-0.5 rounded bg-dark-700 border border-dark-600",
          "opacity-0 group-hover:opacity-100 transition-opacity",
          isResizing && "opacity-100"
        )}>
          <GripHorizontal className="w-4 h-3 text-dark-400" />
        </div>
      </div>

      <div className="p-4 pt-3 flex-1 flex flex-col">
      {/* Pending Images Preview */}
      {pendingImages.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {pendingImages.map((img, idx) => (
            <div key={idx} className="relative group">
              <img
                src={img}
                alt={`Attachment ${idx + 1}`}
                className="w-20 h-20 object-cover rounded-lg border border-dark-600"
              />
              <button
                onClick={() => onRemoveImage(idx)}
                className="absolute -top-2 -right-2 p-1 bg-dark-900 border border-dark-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="w-3 h-3 text-dark-300" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Compact Live Transcription Bar */}
      {(isRecording || isProcessing) && (
        <div className="mb-2 px-3 py-2 bg-dark-800 rounded-lg border border-dark-600">
          {/* Single row: Status | Transcription | Level */}
          <div className="flex items-center gap-3">
            {/* Status indicator */}
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <div className={cn(
                "w-2 h-2 rounded-full",
                isProcessing ? "bg-accent-blue animate-pulse" : "bg-accent-red recording-indicator"
              )} />
              <span className={cn(
                "text-xs font-medium",
                isProcessing ? "text-accent-blue" : "text-accent-red"
              )}>
                {isProcessing ? '⚡' : '●'}
              </span>
              {!isProcessing && (
                <span className="text-[10px] px-1 py-0.5 rounded bg-accent-amber/20 text-accent-amber">
                  {inputMode === 'internal' ? 'BH' : 'Mic'}
                </span>
              )}
            </div>
            
            {/* Transcription text - scrollable single line or wrap */}
            <div className="flex-1 min-w-0 max-h-[60px] overflow-y-auto">
              {liveText && !liveText.includes('🎧') && !liveText.includes('Listening') && !liveText.includes('Processing') ? (
                <p className="text-dark-100 text-sm leading-tight">
                  {liveText}
                  <span className="inline-block w-0.5 h-3 ml-0.5 bg-accent-green animate-pulse" />
                </p>
              ) : (
                <p className="text-dark-500 text-xs italic">
                  {isProcessing ? 'Getting answer...' : 'Listening...'}
                </p>
              )}
            </div>
            
            {/* Audio level bar - compact */}
            {isRecording && !isProcessing && (
              <div className="flex items-center gap-1 flex-shrink-0">
                <div className="w-12 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-accent-green to-accent-amber transition-all duration-100"
                    style={{ width: `${audioLevel}%` }}
                  />
                </div>
              </div>
            )}
            
            {/* Quick hint */}
            <span className="text-[10px] text-dark-500 flex-shrink-0">
              <kbd className="px-1 py-0.5 bg-dark-700 rounded font-mono">`</kbd> send
            </span>
          </div>
        </div>
      )}

      {/* Audio Device Settings (only when not recording) */}
      {showDeviceMenu && !isRecording && (
        <div className="mb-3 p-3 bg-dark-800 rounded-lg border border-dark-600">
          {/* Device Info */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs text-dark-400">Audio Device</span>
            </div>
            <button
              onClick={toggleInputMode}
              className={cn(
                "flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors",
                inputMode === 'internal' 
                  ? "bg-accent-amber/20 text-accent-amber" 
                  : "bg-dark-700 text-dark-300 hover:bg-dark-600"
              )}
            >
              {inputMode === 'internal' ? (
                <>
                  <Volume2 className="w-3.5 h-3.5" />
                  BlackHole
                </>
              ) : (
                <>
                  <Mic className="w-3.5 h-3.5" />
                  Microphone
                </>
              )}
            </button>
          </div>
          
          {/* Current Device */}
          <div className="flex items-center gap-2 text-xs text-dark-400">
            <Headphones className="w-3.5 h-3.5" />
            <span className="truncate">{currentDevice?.label || 'No device selected'}</span>
            {currentDevice?.isBlackHole && (
              <span className="px-1.5 py-0.5 bg-accent-amber/20 text-accent-amber rounded text-[10px]">
                System Audio
              </span>
            )}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-end gap-2">
        {/* File Upload Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-2.5 text-dark-400 hover:text-dark-200 hover:bg-dark-700 rounded-lg transition-colors"
          title="Attach image"
        >
          <Paperclip className="w-5 h-5" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />

        {/* Text Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder={isRecording ? "Recording... Click mic to stop" : "Type your message or paste an image..."}
            disabled={disabled || isRecording}
            className={cn(
              "w-full px-4 py-3 bg-dark-800 border border-dark-600 rounded-xl resize-none",
              "text-dark-100 placeholder-dark-500",
              "focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent",
              "min-h-[48px]",
              "transition-colors",
              (disabled || isRecording) && "opacity-50 cursor-not-allowed"
            )}
            style={{ maxHeight: `${textareaMaxHeight}px` }}
            rows={1}
          />
          
          {/* Audio Level Indicator */}
          {isRecording && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
              <div className="w-16 h-2 bg-dark-700 rounded-full overflow-hidden">
                <div 
                  className="h-full audio-level transition-all duration-100"
                  style={{ width: `${audioLevel}%` }}
                />
              </div>
              <span className="text-xs text-dark-400">{audioLevel}%</span>
            </div>
          )}
        </div>

        {/* Audio Settings Button */}
        <button
          onClick={() => setShowDeviceMenu(!showDeviceMenu)}
          disabled={disabled || isRecording}
          className={cn(
            "p-2.5 rounded-lg transition-all relative",
            showDeviceMenu 
              ? "bg-dark-700 text-dark-200" 
              : "text-dark-400 hover:text-dark-200 hover:bg-dark-700",
            (disabled || isRecording) && "opacity-50 cursor-not-allowed"
          )}
          title="Audio settings"
        >
          <Settings2 className="w-5 h-5" />
          {inputMode === 'internal' && (
            <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-accent-amber rounded-full" />
          )}
        </button>

        {/* Recording Button */}
        <button
          onClick={handleRecordToggle}
          disabled={disabled}
          data-recording-button="true"
          className={cn(
            "p-2.5 rounded-lg transition-all relative",
            isRecording 
              ? "bg-accent-red text-white animate-pulse" 
              : inputMode === 'internal'
                ? "bg-accent-amber/20 text-accent-amber hover:bg-accent-amber/30"
                : "text-dark-400 hover:text-dark-200 hover:bg-dark-700",
            disabled && "opacity-50 cursor-not-allowed"
          )}
          title={isRecording ? "Stop recording (backtick key)" : `Start recording (backtick) - ${inputMode === 'internal' ? 'BlackHole' : 'Mic'}${isStreamReady ? ' ⚡ Ready' : ''}`}
        >
          {isRecording ? (
            <MicOff className="w-5 h-5" />
          ) : inputMode === 'internal' ? (
            <Volume2 className="w-5 h-5" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
          {/* Stream ready indicator */}
          {isStreamReady && !isRecording && (
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-accent-green rounded-full" title="⚡ Ready for instant recording" />
          )}
        </button>

        {/* Send/Stop Button */}
        {isStreaming ? (
          <button
            onClick={onStop}
            className="p-2.5 bg-accent-red hover:bg-accent-red/90 text-white rounded-lg transition-colors"
            title="Stop generating"
          >
            <StopCircle className="w-5 h-5" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={disabled || (!message.trim() && pendingImages.length === 0)}
            className={cn(
              "p-2.5 rounded-lg transition-colors",
              (message.trim() || pendingImages.length > 0) && !disabled
                ? "bg-accent-blue hover:bg-accent-blue/90 text-white"
                : "bg-dark-700 text-dark-500 cursor-not-allowed"
            )}
            title="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Keyboard Hint */}
      <div className="flex items-center justify-between mt-2 text-xs text-dark-500">
        <div className="flex items-center gap-3">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span className="text-dark-600">|</span>
          <span className={cn(
            inputMode === 'internal' && "text-accent-amber"
          )}>
            <kbd className="px-1 py-0.5 bg-dark-800 rounded text-[10px]">`</kbd> to record
            {inputMode === 'internal' && " (BlackHole)"}
          </span>
        </div>
        <span>Cmd+V to paste images</span>
      </div>
      </div>
    </div>
  );
}

