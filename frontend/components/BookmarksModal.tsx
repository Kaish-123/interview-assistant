'use client';

import { useState, useEffect } from 'react';
import { X, Bookmark, BookmarkX, ExternalLink } from 'lucide-react';
import { cn, formatDate, truncate } from '@/lib/utils';
import { chatAPI } from '@/lib/api';
import type { Message } from '@/types';

interface BookmarksModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: number | null;
  onNavigateToMessage: (messageId: number) => void;
  onRemoveBookmark: (messageId: number) => void;
}

export default function BookmarksModal({
  isOpen,
  onClose,
  sessionId,
  onNavigateToMessage,
  onRemoveBookmark,
}: BookmarksModalProps) {
  const [bookmarks, setBookmarks] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && sessionId) {
      loadBookmarks();
    }
  }, [isOpen, sessionId]);

  const loadBookmarks = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      const data = await chatAPI.getBookmarks(sessionId);
      setBookmarks(data as Message[]);
    } catch (error) {
      console.error('Failed to load bookmarks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (messageId: number) => {
    try {
      await chatAPI.toggleBookmark(messageId, false);
      setBookmarks(prev => prev.filter(b => b.id !== messageId));
      onRemoveBookmark(messageId);
    } catch (error) {
      console.error('Failed to remove bookmark:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-900 rounded-xl w-full max-w-lg max-h-[80vh] overflow-hidden shadow-2xl border border-dark-700">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-700">
          <div className="flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-accent-amber" />
            <h2 className="text-lg font-semibold text-dark-100">Bookmarks</h2>
            {bookmarks.length > 0 && (
              <span className="text-sm text-dark-400">({bookmarks.length})</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-dark-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="text-center py-8">
              <p className="text-dark-400">Loading bookmarks...</p>
            </div>
          ) : bookmarks.length === 0 ? (
            <div className="text-center py-8">
              <Bookmark className="w-12 h-12 text-dark-600 mx-auto mb-3" />
              <p className="text-dark-400">No bookmarks yet</p>
              <p className="text-sm text-dark-500 mt-1">
                Click the bookmark icon on any message to save it
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {bookmarks.map((bookmark, index) => (
                <div
                  key={bookmark.id}
                  className="group flex items-start gap-3 p-3 bg-dark-800 hover:bg-dark-700 rounded-lg transition-colors"
                >
                  <div className="flex-shrink-0 w-8 h-8 bg-accent-amber/20 rounded-lg flex items-center justify-center">
                    <span className="text-sm font-medium text-accent-amber">
                      Q{index + 1}
                    </span>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-dark-200 line-clamp-2">
                      {truncate(bookmark.content, 100)}
                    </p>
                    <p className="text-xs text-dark-500 mt-1">
                      {formatDate(bookmark.created_at)}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => {
                        onNavigateToMessage(bookmark.id);
                        onClose();
                      }}
                      className="p-1.5 hover:bg-dark-600 rounded transition-colors"
                      title="Go to message"
                    >
                      <ExternalLink className="w-4 h-4 text-dark-400" />
                    </button>
                    <button
                      onClick={() => handleRemove(bookmark.id)}
                      className="p-1.5 hover:bg-dark-600 rounded transition-colors"
                      title="Remove bookmark"
                    >
                      <BookmarkX className="w-4 h-4 text-accent-red" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-4 border-t border-dark-700 bg-dark-800">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-dark-300 hover:bg-dark-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}




