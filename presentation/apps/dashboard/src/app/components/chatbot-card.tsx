'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { useChatbot } from '@/hooks/use-chatbot';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function ChatbotCard() {
    const { messages, loading, sendMessage } = useChatbot();
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        await sendMessage(input);
        setInput('');
    };

    return (
        <div className="h-full w-full rounded-md border p-4 flex flex-col overflow-hidden">
            <h3 className="mb-4 text-lg font-medium flex-shrink-0">
                AI Chatbot
            </h3>

            {/* Messages container */}
            <div className="flex-1 overflow-y-auto pr-2 space-y-3 min-h-0">
                {messages.length === 0 && (
                    <div className="text-center py-8">
                        <p className="text-gray-500 dark:text-gray-400">
                            No messages yet
                        </p>
                    </div>
                )}

                {messages.length > 0 &&
                    messages.map((m, idx) => (
                        <div
                            key={`${m.timestamp || ''}-${m.role}-${idx}`}
                            className={`max-w-[80%] p-2 text-sm rounded-lg border
                                ${
                                    m.role === 'assistant'
                                        ? 'bg-gray-100 dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-800 dark:text-gray-100'
                                        : 'bg-blue-600 border-blue-700 dark:bg-blue-500 dark:border-blue-600 text-white ml-auto'
                                }
                            `}
                        >
                            <div
                                className="prose prose-sm dark:prose-invert max-w-none
                                    prose-p:my-1 prose-p:leading-relaxed
                                    prose-headings:my-2 prose-headings:font-semibold
                                    prose-ul:my-1 prose-ol:my-1 prose-li:my-0
                                    prose-code:text-xs prose-code:bg-gray-200 dark:prose-code:bg-slate-700 prose-code:px-1 prose-code:py-0.5 prose-code:rounded
                                    prose-pre:my-2 prose-pre:bg-gray-200 dark:prose-pre:bg-slate-700 prose-pre:p-2
                                    prose-blockquote:my-2 prose-blockquote:border-l-4 prose-blockquote:border-gray-300 dark:prose-blockquote:border-slate-600 prose-blockquote:pl-3
                                    prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
                                    prose-strong:font-semibold prose-em:italic
                                    prose-table:my-2 prose-th:border prose-td:border prose-th:p-1 prose-td:p-1"
                            >
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                        // Override code blocks to inherit message background
                                        code: ({
                                            _node,
                                            inline,
                                            ...props
                                        }: any) =>
                                            inline ? (
                                                <code {...props} />
                                            ) : (
                                                <code
                                                    className="block whitespace-pre-wrap"
                                                    {...props}
                                                />
                                            ),
                                    }}
                                >
                                    {m.content}
                                </ReactMarkdown>
                            </div>
                        </div>
                    ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Row */}
            <form
                onSubmit={handleSubmit}
                className="mt-4 flex items-center gap-2 flex-shrink-0"
            >
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={loading}
                    placeholder={
                        loading ? 'Thinking...' : 'Ask about crypto trends...'
                    }
                    className="flex-1 rounded-md border px-3 py-2 text-sm
                               bg-white text-gray-900 border-gray-300
                               dark:bg-slate-800 dark:text-gray-100 dark:border-slate-700
                               focus:outline-none focus:ring-2 focus:ring-blue-400 dark:focus:ring-blue-600
                               disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    aria-label="Send message"
                    className="p-2 rounded-md bg-blue-600 text-white hover:bg-blue-700
                               dark:bg-blue-500 dark:hover:bg-blue-600
                               disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Send size={16} />
                </button>
            </form>
        </div>
    );
}
