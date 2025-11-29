import React from 'react';
import { ChatbotCard } from './chatbot-card';
import { DashboardHeader } from './dashboard-header';
import { DashboardLayout } from './dashboard-layout';
import { NewsFeedCard } from './news-feed-card';
import { RechartCard } from './rechart-card';

export default function Dashboard() {
    // This data could come from a database or API call in a real application
    const chartData = [
        { day: 'Mon', value: 65, color: 'hsl(var(--primary))' },
        { day: 'Tue', value: 85, color: 'hsl(var(--chart-1))' },
        { day: 'Wed', value: 70, color: 'hsl(var(--chart-2))' },
        { day: 'Thu', value: 95, color: 'hsl(var(--chart-3))' },
        { day: 'Fri', value: 45, color: 'hsl(var(--chart-4))' },
    ];

    return (
        <DashboardLayout>
            <DashboardHeader />
            <main className="flex-1 flex flex-col p-8 pt-6">
                <div className="flex items-center justify-between space-y-2 mb-4">
                    <h2 className="text-3xl font-bold tracking-tight">
                        BTC/USD Dashboard
                        {/* TODO: To be replaced with dynamic crypto pair selection */}
                    </h2>
                </div>
                <div className="flex-1 grid gap-4 lg:grid-cols-3 min-h-0">
                    <div className="lg:col-span-2">
                        <RechartCard />
                    </div>

                    <div className="flex flex-col gap-4 h-full min-h-0">
                        <div className="flex-1 min-h-0">
                            <NewsFeedCard />
                        </div>
                        <div className="flex-1 min-h-0">
                            <ChatbotCard />
                        </div>
                    </div>
                </div>
            </main>
        </DashboardLayout>
    );
}
