import { Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/theme-toggle';

export async function DashboardHeader() {
    const user = 'admin';

    return (
        <header className="flex h-14 items-center justify-between border-b bg-background px-6">
            <div>
                A rolling real-time price for major crypto currencies
                {/* TODO: To be implemented */}
            </div>
            <div className="flex items-center gap-4">
                <span className="text-sm">{user}</span>
                <ThemeToggle />
                <Button variant="ghost" size="icon" className="relative">
                    <Bell className="h-4 w-4" />
                    <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-primary" />
                    {/* TODO: Implement Notifications */}
                    <span className="sr-only">Notifications</span>
                </Button>
            </div>
        </header>
    );
}
