'use client';

import { useActivityChat } from '@/contexts/ActivityChatContext';
import { X, Send, Loader2, Copy, Trash2, Save, Anchor, Mic, MicOff, Paperclip, File, FileText, Image as ImageIcon, Download } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import Modal from './Modal';

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
    currentTaskId,
    messages,
    isLoading,
    isAnchored,
    setIsAnchored,
    closeChat,
    sendMessage,
    clearHistory,
    saveTip,
  } = useActivityChat();

  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [uploadedFileUrls, setUploadedFileUrls] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [modalState, setModalState] = useState<{
    isOpen: boolean;
    title?: string;
    message: string;
    type?: 'success' | 'error' | 'info';
  }>({
    isOpen: false,
    message: '',
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  const quickSuggestions = currentTask ? getQuickSuggestions(currentTask) : [];

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        setSpeechSupported(true);
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInput((prev) => prev + (prev ? ' ' : '') + transcript);
          setIsRecording(false);
        };

        recognition.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
          setIsRecording(false);
          if (event.error === 'not-allowed') {
            setModalState({
              isOpen: true,
              title: 'Permission Denied',
              message: 'Microphone access denied. Please allow microphone access in your browser settings.',
              type: 'error',
            });
          }
        };

        recognition.onend = () => {
          setIsRecording(false);
        };

        recognitionRef.current = recognition;
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

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
    if ((!input.trim() && attachedFiles.length === 0) || isLoading) return;

    const message = input.trim();

    // Check if user wants to save the last assistant message
    const saveKeywords = ['save this', 'save that', 'save the tip', 'save this tip', 'save it'];
    if (saveKeywords.some(keyword => message.toLowerCase().includes(keyword))) {
      const lastAssistantMessage = [...messages].reverse().find(m => m.role === 'assistant');
      if (lastAssistantMessage) {
        await handleSaveTip(lastAssistantMessage.content);
        setInput('');
        return;
      }
    }

    // Upload files if any
    let fileAttachments: Array<{ name: string; size: number; url: string }> = [];
    if (attachedFiles.length > 0) {
      const fileUrls = await uploadFiles();
      if (fileUrls.length === 0 && attachedFiles.length > 0) {
        // Upload failed
        return;
      }

      // Create file attachment objects
      fileAttachments = attachedFiles.map((file, index) => ({
        name: file.name,
        size: file.size,
        url: fileUrls[index] || '',
      }));
    }

    // Prepare message with file information
    let fullMessage = message;
    if (fileAttachments.length > 0) {
      fullMessage += '\n\n[Attached files: ' + fileAttachments.map(f => f.name).join(', ') + ']';
    }

    setInput('');
    setAttachedFiles([]);
    setUploadedFileUrls([]);
    await sendMessage(fullMessage, fileAttachments);
  };

  const handleQuickSuggestion = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const copyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setModalState({
        isOpen: true,
        title: 'Success',
        message: 'Copied to clipboard!',
        type: 'success',
      });
    } catch (error) {
      console.error('Failed to copy:', error);
      setModalState({
        isOpen: true,
        title: 'Error',
        message: 'Failed to copy to clipboard.',
        type: 'error',
      });
    }
  };

  const handleSaveTip = async (content: string) => {
    try {
      await saveTip(content);
      setModalState({
        isOpen: true,
        title: 'Success',
        message: 'Tip saved successfully!',
        type: 'success',
      });
    } catch (error) {
      console.error('Failed to save tip:', error);
      setModalState({
        isOpen: true,
        title: 'Error',
        message: 'Failed to save tip. Please try again.',
        type: 'error',
      });
    }
  };

  const handleAnchorClick = () => {
    setIsAnchored(!isAnchored);

    if (!isAnchored && currentTaskId) {
      // Scroll to the task element
      const taskElement = document.querySelector(`[data-task-id="${currentTaskId}"]`);
      if (taskElement) {
        taskElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  const toggleVoiceRecording = () => {
    if (!recognitionRef.current) {
      setModalState({
        isOpen: true,
        title: 'Not Supported',
        message: 'Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.',
        type: 'info',
      });
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Error starting speech recognition:', error);
        setModalState({
          isOpen: true,
          title: 'Error',
          message: 'Failed to start voice recording. Please try again.',
          type: 'error',
        });
      }
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);

    // Validate file count (max 3)
    if (files.length + attachedFiles.length > 3) {
      setModalState({
        isOpen: true,
        title: 'Too Many Files',
        message: 'You can attach up to 3 files at once.',
        type: 'error',
      });
      return;
    }

    // Validate file types
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'image/png', 'image/jpeg', 'image/jpg'];
    const invalidFiles = files.filter(file => !allowedTypes.includes(file.type));

    if (invalidFiles.length > 0) {
      setModalState({
        isOpen: true,
        title: 'Invalid File Type',
        message: 'Only PDF, DOC, DOCX, TXT, PNG, and JPG files are allowed.',
        type: 'error',
      });
      return;
    }

    // Validate file sizes (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    const oversizedFiles = files.filter(file => file.size > maxSize);

    if (oversizedFiles.length > 0) {
      setModalState({
        isOpen: true,
        title: 'File Too Large',
        message: 'Each file must be less than 10MB.',
        type: 'error',
      });
      return;
    }

    // Add files
    setAttachedFiles(prev => [...prev, ...files]);
  };

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async (): Promise<string[]> => {
    if (attachedFiles.length === 0) return [];

    setIsUploading(true);
    const uploadedUrls: string[] = [];

    try {
      for (const file of attachedFiles) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('task_id', currentTaskId || '');

        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/chat/activity/upload`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          uploadedUrls.push(data.file_url);
        } else {
          throw new Error(`Failed to upload ${file.name}`);
        }
      }

      setUploadedFileUrls(uploadedUrls);
      return uploadedUrls;
    } catch (error) {
      console.error('Error uploading files:', error);
      setModalState({
        isOpen: true,
        title: 'Upload Failed',
        message: 'Failed to upload files. Please try again.',
        type: 'error',
      });
      return [];
    } finally {
      setIsUploading(false);
    }
  };

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (['png', 'jpg', 'jpeg'].includes(ext || '')) {
      return <ImageIcon className="w-4 h-4" />;
    } else if (['pdf', 'doc', 'docx', 'txt'].includes(ext || '')) {
      return <FileText className="w-4 h-4" />;
    }
    return <File className="w-4 h-4" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay - only show when not anchored */}
      {!isAnchored && (
        <div
          className="fixed inset-0 bg-black bg-opacity-30 z-40 transition-opacity"
          onClick={closeChat}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed right-0 top-0 h-full bg-white shadow-2xl flex flex-col transform transition-all duration-300 ${
          isAnchored
            ? 'w-full md:w-[600px] z-30' // Side-by-side on desktop
            : 'w-full md:w-[600px] z-50' // Overlay mode
        } ${
          isAnchored
            ? 'md:h-screen max-md:h-1/2 max-md:top-1/2' // Desktop: full height, Mobile: bottom half
            : ''
        }`}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 flex justify-between items-start">
          <div className="flex-1">
            <h2 className="text-lg font-semibold flex items-center gap-3">
              AI Task Assistant
              <button
                onClick={handleAnchorClick}
                className={`relative p-2 rounded-lg transition-all duration-300 group ${
                  isAnchored
                    ? 'bg-orange-500 hover:bg-orange-600 shadow-lg shadow-orange-500/50 animate-pulse'
                    : 'bg-white/10 hover:bg-white/20'
                }`}
                title={isAnchored ? 'Unpin from task' : 'Pin to task'}
              >
                <Anchor className="w-6 h-6" />
                {/* Tooltip */}
                <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  {isAnchored ? 'Unpin from task' : 'Pin to task'}
                </span>
                {/* Glow effect */}
                {isAnchored && (
                  <span className="absolute inset-0 rounded-lg bg-orange-400 blur-md opacity-50 -z-10"></span>
                )}
              </button>
            </h2>
            <button
              onClick={handleAnchorClick}
              className="text-sm text-purple-100 mt-1 line-clamp-2 hover:text-white hover:underline cursor-pointer text-left"
              title="Click to scroll to this task"
            >
              {currentTask}
            </button>
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
                      <div className="mt-2 flex gap-3">
                        <button
                          onClick={() => copyToClipboard(message.content)}
                          className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
                        >
                          <Copy className="w-3 h-3" />
                          Copy
                        </button>
                        <button
                          onClick={() => handleSaveTip(message.content)}
                          className="text-xs text-gray-500 hover:text-purple-700 flex items-center gap-1"
                        >
                          <Save className="w-3 h-3" />
                          Save
                        </button>
                      </div>
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
          {/* Attached Files Display */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-lg px-3 py-2 text-sm"
                >
                  {getFileIcon(file.name)}
                  <div className="flex flex-col">
                    <span className="text-gray-800 font-medium">{file.name}</span>
                    <span className="text-xs text-gray-500">{formatFileSize(file.size)}</span>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="ml-2 text-red-500 hover:text-red-700"
                    title="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2">
            {/* Hidden File Input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />

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
              placeholder={isRecording ? 'Listening...' : 'Ask a question or request help...'}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
              rows={2}
              disabled={isRecording}
            />
            <div className="flex flex-col gap-2">
              {/* File Attachment Button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading || isUploading || attachedFiles.length >= 3}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                title={attachedFiles.length >= 3 ? 'Maximum 3 files allowed' : 'Attach document'}
              >
                <Paperclip className="w-5 h-5" />
              </button>

              {speechSupported && (
                <button
                  onClick={toggleVoiceRecording}
                  disabled={isLoading}
                  className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
                    isRecording
                      ? 'bg-red-600 text-white hover:bg-red-700 animate-pulse'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  title={isRecording ? 'Stop recording' : 'Start voice input'}
                >
                  {isRecording ? (
                    <MicOff className="w-5 h-5" />
                  ) : (
                    <Mic className="w-5 h-5" />
                  )}
                </button>
              )}
              <button
                onClick={handleSend}
                disabled={(!input.trim() && attachedFiles.length === 0) || isLoading || isUploading}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {isLoading || isUploading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {isRecording
              ? '🎤 Recording... Speak now'
              : `Press Enter to send, Shift+Enter for new line${speechSupported ? ', or click mic for voice input' : ''}`
            }
          </p>
        </div>
      </div>

      {/* Modal */}
      <Modal
        isOpen={modalState.isOpen}
        onClose={() => setModalState({ ...modalState, isOpen: false })}
        title={modalState.title}
        message={modalState.message}
        type={modalState.type}
      />
    </>
  );
}
