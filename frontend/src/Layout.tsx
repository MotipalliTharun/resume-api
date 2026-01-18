import { Outlet } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';

export function Layout() {
    return (
        <div className="flex h-screen bg-[#f8fafc] overflow-hidden font-sans">
            <Sidebar />
            {/* Main Content Area */}
            <div className="flex-1 ml-20 md:ml-64 relative overflow-y-auto w-full">
                <Outlet />
            </div>
        </div>
    );
}
