import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { AccessModal } from './components/AccessModal';
import { SettingsModal } from './components/SettingsModal';
import { getAccessToken } from './utils/api';

export function Layout() {
    const [isAuthorized, setIsAuthorized] = useState(!!getAccessToken());
    const [showSettings, setShowSettings] = useState(false);

    useEffect(() => {
        const checkAuth = () => {
            setIsAuthorized(!!getAccessToken());
        };

        window.addEventListener('storage', checkAuth);
        window.addEventListener('auth-error', () => setIsAuthorized(false));

        return () => {
            window.removeEventListener('storage', checkAuth);
            window.removeEventListener('auth-error', () => setIsAuthorized(false));
        };
    }, []);

    return (
        <div className="flex h-screen bg-[#f8fafc] overflow-hidden font-sans">
            {/* {!isAuthorized && <AccessModal onSuccess={() => setIsAuthorized(true)} />} - Global Lock Removed */}
            {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}

            <Sidebar onSettingsClick={() => setShowSettings(true)} />

            {/* Main Content Area */}
            <div className={`flex-1 ml-20 md:ml-64 relative overflow-y-auto w-full transition-opacity ${!isAuthorized ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
                <Outlet />
            </div>
        </div>
    );
}
