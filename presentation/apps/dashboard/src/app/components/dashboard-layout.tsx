'use client';

import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

interface DashboardLayoutProps {
    children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
    return (
        <SidebarProvider>
            <div className="flex h-screen w-full overflow-hidden">
                <SidebarInset className="flex w-full flex-col overflow-hidden">
                    {children}
                </SidebarInset>
            </div>
        </SidebarProvider>
    );
}
