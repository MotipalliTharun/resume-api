import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { SettingsModal } from './components/SettingsModal';

export function Layout() {
    const [showSettings, setShowSettings] = useState(false);

    return (
        <div className="flex h-screen bg-[#f8fafc] overflow-hidden font-sans">
            {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}

            <Sidebar onSettingsClick={() => setShowSettings(true)} />

            {/* Main Content Area */}
            <div className={`flex-1 ml-20 md:ml-64 relative overflow-y-auto w-full transition-opacity opacity-100`}>
                <Outlet />
            </div>
        </div>
    );
}
