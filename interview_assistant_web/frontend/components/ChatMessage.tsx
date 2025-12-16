'use client';

import { useState } from 'react';
import { User, Bot, Bookmark, BookmarkCheck, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { cn, formatDate, copyToClipboard } from '@/lib/utils';
import type { Message } from '@/types';

interface ChatMessageProps {
  message: Message;
  onToggleBookmark?: (messageId: number, isBookmarked: boolean) => void;
  fontSize?: number;
}

export default function ChatMessage({ message, onToggleBookmark, fontSize = 14 }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  const handleCopy = async () => {
    await copyToClipboard(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleBookmark = () => {
    if (onToggleBookmark) {
      onToggleBookmark(message.id, !message.is_bookmarked);
    }
  };

  // Don't display system messages
  if (isSystem) return null;

  return (
    <div
      className={cn(
        "group py-6 px-4 md:px-8 animate-fade-in",
        isUser ? "bg-dark-800" : "bg-dark-900",
        message.is_bookmarked && "bookmark-highlight"
      )}
    >
      <div className="max-w-4xl mx-auto flex gap-4">
        {/* Avatar */}
        <div className={cn(
          "flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center",
          isUser ? "bg-accent-blue" : "bg-accent-green"
        )}>
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <span className="font-medium text-dark-100">
              {isUser ? 'You' : 'Assistant'}
            </span>
            <span className="text-xs text-dark-500">
              {formatDate(message.created_at)}
            </span>
          </div>

          {/* Message content */}
          <div 
            className="message-content prose prose-invert max-w-none"
            style={{ fontSize: `${fontSize}px` }}
          >
            {/* Images */}
            {message.images && message.images.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {message.images.map((img, idx) => (
                  <img
                    key={idx}
                    src={img}
                    alt={`Attachment ${idx + 1}`}
                    className="max-w-xs max-h-48 rounded-lg border border-dark-700"
                  />
                ))}
              </div>
            )}

            {/* Text content with markdown */}
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={oneDark}
                      language={match[1]}
                      PreTag="div"
                      customStyle={{
                        margin: 0,
                        borderRadius: '0.5rem',
                        fontSize: `${fontSize - 1}px`,
                      }}
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
                p({ children }) {
                  return <p className="mb-3 last:mb-0">{children}</p>;
                },
                ul({ children }) {
                  return <ul className="list-disc ml-4 mb-3">{children}</ul>;
                },
                ol({ children }) {
                  return <ol className="list-decimal ml-4 mb-3">{children}</ol>;
                },
                li({ children }) {
                  return <li className="mb-1">{children}</li>;
                },
                h1({ children }) {
                  return <h1 className="text-xl font-bold mb-3 mt-4">{children}</h1>;
                },
                h2({ children }) {
                  return <h2 className="text-lg font-bold mb-2 mt-3">{children}</h2>;
                },
                h3({ children }) {
                  return <h3 className="text-base font-bold mb-2 mt-2">{children}</h3>;
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2 py-1 text-xs text-dark-400 hover:text-dark-200 hover:bg-dark-700 rounded transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-accent-green" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  Copy
                </>
              )}
            </button>
            
            {!isUser && (
              <button
                onClick={handleBookmark}
                className={cn(
                  "flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors",
                  message.is_bookmarked 
                    ? "text-accent-amber hover:bg-dark-700" 
                    : "text-dark-400 hover:text-dark-200 hover:bg-dark-700"
                )}
              >
                {message.is_bookmarked ? (
                  <>
                    <BookmarkCheck className="w-3.5 h-3.5" />
                    Bookmarked
                  </>
                ) : (
                  <>
                    <Bookmark className="w-3.5 h-3.5" />
                    Bookmark
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}





