'use client';

import { useState, useEffect } from 'react';
import { X, BarChart3, AlertTriangle, CheckCircle, RefreshCw, Zap } from 'lucide-react';
import { cn, formatTokenCount } from '@/lib/utils';
import { chatAPI } from '@/lib/api';
import type { PerformanceDiagnostic } from '@/types';

interface DiagnosticsModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: number | null;
  onSummarize: () => void;
  onNewChat: () => void;
}

export default function DiagnosticsModal({
  isOpen,
  onClose,
  sessionId,
  onSummarize,
  onNewChat,
}: DiagnosticsModalProps) {
  const [diagnostic, setDiagnostic] = useState<PerformanceDiagnostic | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && sessionId) {
      loadDiagnostics();
    }
  }, [isOpen, sessionId]);

  const loadDiagnostics = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      const data = await chatAPI.getDiagnostics(sessionId);
      setDiagnostic(data as PerformanceDiagnostic);
    } catch (error) {
      console.error('Failed to load diagnostics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const tokenReduction = diagnostic && diagnostic.estimated_total_tokens > 0
    ? ((1 - diagnostic.will_send_tokens / diagnostic.estimated_total_tokens) * 100).toFixed(0)
    : 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-900 rounded-xl w-full max-w-lg max-h-[80vh] overflow-hidden shadow-2xl border border-dark-700">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-700">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-accent-blue" />
            <h2 className="text-lg font-semibold text-dark-100">Performance Diagnostics</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-dark-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 text-accent-blue animate-spin" />
            </div>
          ) : diagnostic ? (
            <div className="space-y-4">
              {/* Message Stats */}
              <div className="bg-dark-800 rounded-lg p-4">
                <h3 className="text-sm font-medium text-dark-300 mb-3">Chat Statistics</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-dark-500">Total Messages</p>
                    <p className="text-lg font-semibold text-dark-100">{diagnostic.total_messages}</p>
                  </div>
                  <div>
                    <p className="text-xs text-dark-500">Images</p>
                    <p className="text-lg font-semibold text-dark-100">{diagnostic.images_count}</p>
                  </div>
                  <div>
                    <p className="text-xs text-dark-500">User Messages</p>
                    <p className="text-lg font-semibold text-dark-100">{diagnostic.user_messages}</p>
                  </div>
                  <div>
                    <p className="text-xs text-dark-500">Assistant Messages</p>
                    <p className="text-lg font-semibold text-dark-100">{diagnostic.assistant_messages}</p>
                  </div>
                </div>
              </div>

              {/* Token Usage */}
              <div className="bg-dark-800 rounded-lg p-4">
                <h3 className="text-sm font-medium text-dark-300 mb-3">Token Usage</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-dark-400">Full Chat Tokens</span>
                    <span className={cn(
                      "text-sm font-medium",
                      diagnostic.estimated_total_tokens > 30000 ? "text-accent-red" : "text-dark-200"
                    )}>
                      ~{formatTokenCount(diagnostic.estimated_total_tokens)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-dark-400">→ Will Send</span>
                    <span className={cn(
                      "text-sm font-medium",
                      diagnostic.will_send_tokens > 15000 ? "text-accent-amber" : "text-accent-green"
                    )}>
                      ~{formatTokenCount(diagnostic.will_send_tokens)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-dark-400">Token Reduction</span>
                    <span className="text-sm font-medium text-accent-green">
                      {tokenReduction}% saved!
                    </span>
                  </div>
                </div>
              </div>

              {/* Optimization Status */}
              <div className="bg-dark-800 rounded-lg p-4">
                <h3 className="text-sm font-medium text-dark-300 mb-3">Optimization</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-dark-400">Fast Mode</span>
                    <span className={cn(
                      "text-sm font-medium",
                      diagnostic.optimization_mode ? "text-accent-amber" : "text-dark-500"
                    )}>
                      {diagnostic.optimization_mode ? '⚡ ON' : '🐢 OFF'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-dark-400">Has Summary</span>
                    <span className={cn(
                      "text-sm font-medium",
                      diagnostic.has_summary ? "text-accent-green" : "text-dark-500"
                    )}>
                      {diagnostic.has_summary ? '✅ Yes' : '❌ No'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-dark-400">Messages to API</span>
                    <span className="text-sm font-medium text-dark-200">
                      {diagnostic.will_send_messages}/{diagnostic.total_messages}
                    </span>
                  </div>
                </div>
              </div>

              {/* Issues & Recommendations */}
              {(diagnostic.issues.length > 0 || diagnostic.recommendations.length > 0) && (
                <div className="bg-dark-800 rounded-lg p-4">
                  {diagnostic.issues.length > 0 && (
                    <>
                      <h3 className="text-sm font-medium text-accent-amber mb-2 flex items-center gap-1">
                        <AlertTriangle className="w-4 h-4" />
                        Issues Found
                      </h3>
                      <ul className="list-disc list-inside space-y-1 mb-3">
                        {diagnostic.issues.map((issue, i) => (
                          <li key={i} className="text-sm text-dark-300">{issue}</li>
                        ))}
                      </ul>
                    </>
                  )}
                  
                  {diagnostic.recommendations.length > 0 && (
                    <>
                      <h3 className="text-sm font-medium text-accent-blue mb-2">💡 Recommendations</h3>
                      <ul className="list-disc list-inside space-y-1">
                        {diagnostic.recommendations.map((rec, i) => (
                          <li key={i} className="text-sm text-dark-300">{rec}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              )}

              {diagnostic.issues.length === 0 && (
                <div className="flex items-center gap-2 p-4 bg-accent-green/10 rounded-lg border border-accent-green/30">
                  <CheckCircle className="w-5 h-5 text-accent-green" />
                  <span className="text-sm text-accent-green">No performance issues detected!</span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-center text-dark-400 py-8">No session selected</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-dark-700 bg-dark-800">
          <button
            onClick={() => {
              onSummarize();
              loadDiagnostics();
            }}
            className="flex items-center gap-1 px-4 py-2 text-sm bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-lg transition-colors"
          >
            <Zap className="w-4 h-4" />
            Force Summarize
          </button>
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="flex items-center gap-1 px-4 py-2 text-sm bg-accent-blue hover:bg-accent-blue/90 text-white rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            New Chat
          </button>
        </div>
      </div>
    </div>
  );
}





