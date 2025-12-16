'use client';

import { X, Keyboard } from 'lucide-react';
import { cn } from '@/lib/utils';

interface HotkeysHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const HOTKEY_SECTIONS = [
  {
    title: '🎤 Recording',
    shortcuts: [
      { keys: ['`'], description: 'Start/Stop Recording' },
      { keys: ['~'], description: 'Force Stop Recording' },
      { keys: ['Shift', '1'], description: 'Capture Screenshot' },
    ],
  },
  {
    title: '⌨️ Quick Access (Number Combos)',
    shortcuts: [
      { keys: ['1', '2'], description: 'Focus Chat Input' },
      { keys: ['2', '3'], description: 'Upload Resume/JD' },
      { keys: ['3', '4'], description: 'Toggle Fast Mode' },
      { keys: ['4', '5'], description: 'Record with BlackHole (Internal)' },
      { keys: ['5', '6'], description: 'Record with Microphone (External)' },
    ],
  },
  {
    title: '🚀 Commands',
    shortcuts: [
      { keys: ['⌘/Ctrl', 'N'], description: 'New Chat' },
      { keys: ['⌘/Ctrl', 'Shift', 'S'], description: 'Quick Setup' },
      { keys: ['⌘/Ctrl', 'B'], description: 'Add Bookmark' },
      { keys: ['⌘/Ctrl', 'M'], description: 'Toggle Model' },
      { keys: ['⌘/Ctrl', 'D'], description: 'Performance Diagnostics' },
      { keys: ['⌘/Ctrl', 'P'], description: 'Toggle Sidebar' },
      { keys: ['⌘/Ctrl', 'Shift', 'C'], description: 'Copy Last Response' },
    ],
  },
  {
    title: '🔤 Font Size',
    shortcuts: [
      { keys: ['⌘/Ctrl', '='], description: 'Increase Font Size' },
      { keys: ['⌘/Ctrl', '-'], description: 'Decrease Font Size' },
    ],
  },
  {
    title: '⚡ Function Keys',
    shortcuts: [
      { keys: ['F2'], description: '💾 Save UI Layout (persists on reload)' },
      { keys: ['F4'], description: 'Add Bookmark' },
      { keys: ['F5'], description: 'Toggle Bookmarks Panel' },
      { keys: ['F6'], description: 'Quick Setup' },
      { keys: ['F7'], description: 'Toggle Fast Mode' },
      { keys: ['F8'], description: 'New Chat' },
      { keys: ['Esc'], description: 'Focus Input / Close Modals' },
    ],
  },
  {
    title: '🔄 Chat Navigation',
    shortcuts: [
      { keys: ['PageDown'], description: 'Scroll to Bottom of Chat' },
      { keys: ['PageUp'], description: 'Scroll to Top of Chat' },
      { keys: ['End'], description: 'Scroll to Bottom (alternate)' },
      { keys: ['Home'], description: 'Scroll to Top (alternate)' },
    ],
  },
  {
    title: '📝 Chat Input',
    shortcuts: [
      { keys: ['Enter'], description: 'Send Message' },
      { keys: ['Shift', 'Enter'], description: 'New Line' },
      { keys: ['⌘/Ctrl', 'V'], description: 'Paste (supports images)' },
    ],
  },
];

export default function HotkeysHelpModal({ isOpen, onClose }: HotkeysHelpModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-dark-800 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden border border-dark-600 animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-600 bg-dark-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-accent-blue/20 rounded-lg">
              <Keyboard className="w-5 h-5 text-accent-blue" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-dark-100">Keyboard Shortcuts</h2>
              <p className="text-sm text-dark-400">Master the Interview Assistant with hotkeys</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-dark-400 hover:text-dark-200 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(85vh-80px)]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {HOTKEY_SECTIONS.map((section, sectionIndex) => (
              <div 
                key={sectionIndex}
                className={cn(
                  "p-4 rounded-xl bg-dark-900/50 border border-dark-700",
                  sectionIndex === 0 && "md:col-span-1",
                )}
              >
                <h3 className="text-sm font-semibold text-dark-200 mb-3 pb-2 border-b border-dark-700">
                  {section.title}
                </h3>
                <div className="space-y-2">
                  {section.shortcuts.map((shortcut, shortcutIndex) => (
                    <div 
                      key={shortcutIndex}
                      className="flex items-center justify-between gap-4 py-1.5"
                    >
                      <span className="text-sm text-dark-300">{shortcut.description}</span>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {shortcut.keys.map((key, keyIndex) => (
                          <span key={keyIndex} className="flex items-center">
                            <kbd className={cn(
                              "px-2 py-1 text-xs font-mono rounded",
                              "bg-dark-700 text-dark-200 border border-dark-600",
                              "shadow-sm"
                            )}>
                              {key}
                            </kbd>
                            {keyIndex < shortcut.keys.length - 1 && (
                              <span className="mx-1 text-dark-500">+</span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          
          {/* Tips */}
          <div className="mt-6 p-4 rounded-xl bg-accent-blue/10 border border-accent-blue/20">
            <h4 className="text-sm font-semibold text-accent-blue mb-2">💡 Pro Tips</h4>
            <ul className="text-sm text-dark-300 space-y-1">
              <li>• Number combos (1+2, 2+3, etc.) work by pressing both keys together</li>
              <li>• <kbd className="px-1 py-0.5 text-xs bg-dark-700 rounded">5</kbd>+<kbd className="px-1 py-0.5 text-xs bg-dark-700 rounded">6</kbd> records with your mic (for your voice)</li>
              <li>• <kbd className="px-1 py-0.5 text-xs bg-dark-700 rounded">4</kbd>+<kbd className="px-1 py-0.5 text-xs bg-dark-700 rounded">5</kbd> records with BlackHole (for system/Zoom audio)</li>
              <li>• <kbd className="px-1 py-0.5 text-xs bg-dark-700 rounded">F2</kbd> saves your UI layout (sidebar width, chat input size) - persists on reload!</li>
              <li>• Use <kbd className="px-1 py-0.5 text-xs bg-dark-700 rounded">⌘</kbd> on Mac or <kbd className="px-1 py-0.5 text-xs bg-dark-700 rounded">Ctrl</kbd> on Windows</li>
              <li>• Press <kbd className="px-1 py-0.5 text-xs bg-dark-700 rounded">?</kbd> anytime to show this help</li>
              <li>• Hotkeys work globally except when typing in input fields</li>
            </ul>
          </div>
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t border-dark-600 bg-dark-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-accent-blue hover:bg-accent-blue/90 text-white rounded-lg transition-colors text-sm font-medium"
          >
            Got it!
          </button>
        </div>
      </div>
    </div>
  );
}



