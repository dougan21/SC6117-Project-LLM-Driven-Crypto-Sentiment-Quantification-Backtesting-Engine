'use client';

import React, { useState } from 'react';
import { Send } from 'lucide-react';

export function ChatbotCard() {
    const [messages] = useState([
        { role: 'assistant', content: 'Hello! How can I help you today?' },
        { role: 'user', content: 'Tell me about this dashboard.' },
        {
            role: 'assistant',
            content: 'Sorry, this feature is still under development.',
        },
    ]);

    return (
        <div className="h-full w-full rounded-md border p-4 flex flex-col min-h-0">
            <h3 className="mb-4 text-lg font-medium flex-shrink-0">
                AI Chatbot
            </h3>

            {/* Messages container */}
            <div className="flex-1 w-full overflow-y-auto pr-2 space-y-3 min-h-0">
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
                            key={idx}
                            className={`max-w-[80%] p-2 text-sm rounded-lg border
                                ${
                                    m.role === 'assistant'
                                        ? 'bg-gray-100 dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-800 dark:text-gray-100'
                                        : 'bg-blue-600 border-blue-700 dark:bg-blue-500 dark:border-blue-600 text-white ml-auto'
                                }
                            `}
                        >
                            {m.content}
                        </div>
                    ))}
            </div>

            {/* Input Row */}
            <div className="mt-4 flex items-center gap-2 flex-shrink-0">
                <input
                    type="text"
                    placeholder="Type a message..."
                    className="flex-1 rounded-md border px-3 py-2 text-sm
                               bg-white text-gray-900 border-gray-300
                               dark:bg-slate-800 dark:text-gray-100 dark:border-slate-700
                               focus:outline-none focus:ring-2 focus:ring-blue-400 dark:focus:ring-blue-600"
                />
                <button
                    className="p-2 rounded-md bg-blue-600 text-white hover:bg-blue-700
                               dark:bg-blue-500 dark:hover:bg-blue-600"
                >
                    <Send size={16} />
                </button>
            </div>
        </div>
    );
}
