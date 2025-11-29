import type { Metadata } from 'next';
import DashboardPage from './components/dashboard-page';

export const metadata: Metadata = {
    title: 'Team 1 Demo Dashboard',
};

export default function Dashboard() {
    return <DashboardPage />;
}
