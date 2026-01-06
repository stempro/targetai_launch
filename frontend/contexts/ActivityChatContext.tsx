'use client';

import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { weeklyLogsApi } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface FileAttachment {
  name: string;
  size: number;
  url: string;
}

interface ActivityChatContextType {
  isOpen: boolean;
  currentTask: string | null;
  currentTaskId: string | null;
  messages: Message[];
  isLoading: boolean;
  isAnchored: boolean;
  setIsAnchored: (anchored: boolean) => void;
  openChat: (task: string, taskId: string) => void;
  closeChat: () => void;
  sendMessage: (content: string, fileAttachments?: FileAttachment[]) => Promise<void>;
  clearHistory: () => void;
  saveTip: (content: string) => Promise<void>;
}

const ActivityChatContext = createContext<ActivityChatContextType | undefined>(undefined);

export function ActivityChatProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentTask, setCurrentTask] = useState<string | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnchored, setIsAnchored] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const openChat = useCallback(async (task: string, taskId: string) => {
    setCurrentTask(task);
    setCurrentTaskId(taskId);
    setIsOpen(true);
    setIsLoading(true);

    try {
      // Load conversation history for this task
      const res = await weeklyLogsApi.getChatHistory(taskId);
      if (res.data && res.data.messages) {
        setMessages(res.data.messages);
      } else {
        // Start with pre-written recommendation as first message
        setMessages([
          {
            role: 'assistant',
            content: `I'm here to help you with: "${task}"\n\nLet me provide some initial guidance...\n\n(Loading recommendations...)`,
            timestamp: new Date().toISOString(),
          },
        ]);

        // Load the pre-written recommendation
        const recommendationRes = await fetch('/api/chat/activity/recommendation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task_description: task }),
        });

        if (recommendationRes.ok) {
          const data = await recommendationRes.json();
          setMessages([
            {
              role: 'assistant',
              content: data.recommendation,
              timestamp: new Date().toISOString(),
            },
          ]);
        }
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
      setMessages([
        {
          role: 'assistant',
          content: `I'm here to help you with: "${task}"\n\nWhat questions do you have?`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const closeChat = useCallback(() => {
    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsOpen(false);
    setIsAnchored(false);
  }, []);

  const sendMessage = useCallback(
    async (content: string, fileAttachments?: FileAttachment[]) => {
      if (!currentTaskId || !currentTask) return;

      // Add user message immediately
      const userMessage: Message = {
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      // Create abort controller for this request
      abortControllerRef.current = new AbortController();

      try {
        // Add placeholder for assistant message
        const assistantMessageId = Date.now();
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
          },
        ]);

        // Stream the response
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/chat/activity/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task_id: currentTaskId,
            task_description: currentTask,
            message: content,
            history: messages,
            file_attachments: fileAttachments || [],
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error('Failed to get response');
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let accumulatedContent = '';

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.chunk) {
                    accumulatedContent += data.chunk;
                    // Update the last message with accumulated content
                    setMessages((prev) => {
                      const updated = [...prev];
                      updated[updated.length - 1] = {
                        role: 'assistant',
                        content: accumulatedContent,
                        timestamp: new Date().toISOString(),
                      };
                      return updated;
                    });
                  }
                  if (data.done) {
                    break;
                  }
                } catch (e) {
                  // Skip invalid JSON
                }
              }
            }
          }
        }

        // Save conversation to backend
        await weeklyLogsApi.saveChatHistory(currentTaskId, {
          task_id: currentTaskId,
          task_description: currentTask,
          messages: [...messages, userMessage, { role: 'assistant', content: accumulatedContent, timestamp: new Date().toISOString() }],
        });
      } catch (error: any) {
        if (error.name === 'AbortError') {
          console.log('Request cancelled');
        } else {
          console.error('Error sending message:', error);
          setMessages((prev) => [
            ...prev.slice(0, -1),
            {
              role: 'assistant',
              content: 'Sorry, I encountered an error. Please try again.',
              timestamp: new Date().toISOString(),
            },
          ]);
        }
      } finally {
        setIsLoading(false);
        abortControllerRef.current = null;
      }
    },
    [currentTaskId, currentTask, messages]
  );

  const clearHistory = useCallback(() => {
    setMessages([]);
  }, []);

  const saveTip = useCallback(
    async (content: string) => {
      if (!currentTaskId) {
        throw new Error('No task selected');
      }

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/chat/activity/save-tip/${currentTaskId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save tip');
      }

      return response.json();
    },
    [currentTaskId]
  );

  return (
    <ActivityChatContext.Provider
      value={{
        isOpen,
        currentTask,
        currentTaskId,
        messages,
        isLoading,
        isAnchored,
        setIsAnchored,
        openChat,
        closeChat,
        sendMessage,
        clearHistory,
        saveTip,
      }}
    >
      {children}
    </ActivityChatContext.Provider>
  );
}

export function useActivityChat() {
  const context = useContext(ActivityChatContext);
  if (!context) {
    throw new Error('useActivityChat must be used within ActivityChatProvider');
  }
  return context;
}
