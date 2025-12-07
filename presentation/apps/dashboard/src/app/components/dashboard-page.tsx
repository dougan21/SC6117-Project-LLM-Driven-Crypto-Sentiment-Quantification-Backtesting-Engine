'use client';
import React, { useState } from 'react';
import { ChatbotCard } from './chatbot-card';
import { DashboardHeader } from './dashboard-header';
import { DashboardLayout } from './dashboard-layout';
import { NewsFeedCard } from './news-feed-card';
import { RechartCard } from './rechart-card';

export default function Dashboard() {
    const [cryptoPair, setCryptoPair] = useState('BTC/USD');

    return (
        <DashboardLayout>
            <DashboardHeader />
            <main className="flex-1 flex flex-col p-8 pt-6 overflow-hidden">
                <div className="flex items-center justify-between mb-4 flex-shrink-0">
                    <h2 className="text-3xl font-bold tracking-tight">
                        {cryptoPair} Dashboard
                    </h2>
                </div>
                <div className="flex-1 grid gap-4 lg:grid-cols-3 min-h-0">
                    <div className="lg:col-span-2 min-h-0 overflow-hidden">
                        <RechartCard onCryptoPairChange={setCryptoPair} />
                    </div>

                    <div className="flex flex-col gap-4 min-h-0 overflow-hidden">
                        <div className="flex-1 min-h-0 overflow-hidden">
                            <NewsFeedCard />
                        </div>
                        <div className="flex-1 min-h-0 overflow-hidden">
                            <ChatbotCard />
                        </div>
                    </div>
                </div>
            </main>
        </DashboardLayout>
    );
}
