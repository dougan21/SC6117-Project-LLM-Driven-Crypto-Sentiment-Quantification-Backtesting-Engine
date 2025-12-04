'use client';

import { useState } from 'react';

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

export interface ChatResponse {
    message: string;
    timestamp: string;
}

const CHATBOT_API = '/api/chatbot';

const INITIAL_MESSAGE_CONTENT =
    'Hello! I can help you analyze cryptocurrency trends and answer questions about the market. Ask me anything!';

function createInitialMessage(): ChatMessage {
    return {
        role: 'assistant',
        content: INITIAL_MESSAGE_CONTENT,
        timestamp: new Date().toISOString(),
    };
}

/**
 * Hook for managing chatbot interactions
 * Handles message sending, history, and API communication
 */
export function useChatbot() {
    const [messages, setMessages] = useState<ChatMessage[]>([
        createInitialMessage(),
    ]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const sendMessage = async (content: string) => {
        if (!content.trim()) return;

        // Add user message immediately
        const userMessage: ChatMessage = {
            role: 'user',
            content: content.trim(),
            timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);

        try {
            setLoading(true);
            setError(null);

            const response = await fetch(CHATBOT_API, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: content.trim(),
                    history: messages,
                }),
            });

            if (!response.ok) {
                throw new Error(
                    `Failed to send message: ${response.statusText}`
                );
            }

            const data: ChatResponse = await response.json();

            // Add assistant response
            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: data.message,
                timestamp: data.timestamp,
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (err) {
            const errorMessage =
                err instanceof Error ? err.message : 'Unknown error';
            setError(err instanceof Error ? err : new Error(errorMessage));

            // Add error message as assistant response
            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: `Sorry, I encountered an error: ${errorMessage}. This feature is still under development.`,
                timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } finally {
            setLoading(false);
        }
    };

    const clearMessages = () => {
        setMessages([createInitialMessage()]);
        setError(null);
    };

    return {
        messages,
        loading,
        error,
        sendMessage,
        clearMessages,
    };
}
