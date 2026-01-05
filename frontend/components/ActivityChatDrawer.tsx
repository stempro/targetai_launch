'use client';

import { useActivityChat } from '@/contexts/ActivityChatContext';
import { X, Send, Loader2, Copy, Trash2 } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

const QUICK_SUGGESTIONS: Record<string, string[]> = {
  'optimize linkedin': [
    'Show me a good headline example',
    'What should I include in About section?',
    'How do I add credibility signals?',
  ],
  'build target list': [
    'Where can I find counselors?',
    'What are the scoring criteria?',
    'How do I qualify prospects?',
  ],
  'send connection': [
    'Give me a connection message template',
    'How do I personalize my approach?',
    'What response rate should I expect?',
  ],
  'engage with posts': [
    'What makes a meaningful comment?',
    'Show me good comment examples',
    'When should I comment?',
  ],
  'draft and publish': [
    'Give me topic ideas',
    'Show me an example opening',
    'When should I post?',
  ],
  'prepare demo': [
    'What sample data should I create?',
    'How do I structure the demo?',
    'What should I practice?',
  ],
};

function getQuickSuggestions(task: string): string[] {
  const taskLower = task.toLowerCase();
  for (const [key, suggestions] of Object.entries(QUICK_SUGGESTIONS)) {
    if (taskLower.includes(key)) {
      return suggestions;
    }
  }
  return [
    'How do I get started?',
    'What are the key steps?',
    'Can you give me an example?',
  ];
}

export default function ActivityChatDrawer() {
  const {
    isOpen,
    currentTask,
    messages,
    isLoading,
    closeChat,
    sendMessage,
    clearHistory,
  } = useActivityChat();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const quickSuggestions = currentTask ? getQuickSuggestions(currentTask) : [];

  useEffect(() => {
    if (isOpen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const message = input.trim();
    setInput('');
    await sendMessage(message);
  };

  const handleQuickSuggestion = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const copyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      alert('Copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-30 z-40 transition-opacity"
        onClick={closeChat}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-full md:w-[600px] bg-white shadow-2xl z-50 flex flex-col transform transition-transform">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 flex justify-between items-start">
          <div className="flex-1">
            <h2 className="text-lg font-semibold">AI Task Assistant</h2>
            <p className="text-sm text-purple-100 mt-1 line-clamp-2">
              {currentTask}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={clearHistory}
              className="p-2 hover:bg-white/20 rounded transition-colors"
              title="Clear history"
            >
              <Trash2 className="w-5 h-5" />
            </button>
            <button
              onClick={closeChat}
              className="p-2 hover:bg-white/20 rounded transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-800 border border-gray-200'
                }`}
              >
                {message.role === 'assistant' ? (
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
                        li: ({ children }) => <li className="mb-1">{children}</li>,
                        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                        code: ({ children }) => (
                          <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">
                            {children}
                          </code>
                        ),
                        pre: ({ children }) => (
                          <pre className="bg-gray-100 p-2 rounded overflow-x-auto text-sm">
                            {children}
                          </pre>
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                    {message.content && (
                      <button
                        onClick={() => copyToClipboard(message.content)}
                        className="mt-2 text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
                      >
                        <Copy className="w-3 h-3" />
                        Copy
                      </button>
                    )}
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                )}
              </div>
            </div>
          ))}

          {isLoading && messages[messages.length - 1]?.role === 'user' && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-800 border border-gray-200 rounded-lg p-3">
                <Loader2 className="w-5 h-5 animate-spin text-purple-600" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestions */}
        {quickSuggestions.length > 0 && !isLoading && (
          <div className="px-4 py-2 bg-white border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-2">Quick suggestions:</p>
            <div className="flex flex-wrap gap-2">
              {quickSuggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickSuggestion(suggestion)}
                  className="text-xs bg-purple-100 text-purple-700 px-3 py-1.5 rounded-full hover:bg-purple-200 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a question or request help..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
              rows={2}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </>
  );
}
