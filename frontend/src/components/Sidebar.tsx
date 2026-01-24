import { NavLink } from 'react-router-dom';
import { Home, History, BarChart3, Settings, FileText } from 'lucide-react';

interface SidebarProps {
    onSettingsClick: () => void;
}

export function Sidebar({ onSettingsClick }: SidebarProps) {
    const navItems = [
        { icon: Home, label: 'Resume Tailor', path: '/' },
        { icon: History, label: 'Application Tracker', path: '/tracker' },
        { icon: FileText, label: 'Cover Letter', path: '/cover-letter' },
        { icon: BarChart3, label: 'Analysis & Stats', path: '/analysis' },
    ];

    return (
        <aside className="fixed left-0 top-0 h-screen w-20 md:w-64 bg-slate-900/90 backdrop-blur-xl border-r border-slate-700/50 flex flex-col z-50 transition-all duration-300">
            <div className="p-6 flex items-center justify-center md:justify-start gap-3 border-b border-slate-700/50">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                    <span className="text-white font-bold text-xl">R</span>
                </div>
                <span className="hidden md:block text-slate-100 font-bold text-lg tracking-tight">ResumeAI</span>
            </div>

            <nav className="flex-1 py-6 px-3 flex flex-col gap-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => `
              flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group
              ${isActive
                                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-lg shadow-blue-500/5'
                                : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50 hover:translate-x-1'
                            }
            `}
                    >
                        <item.icon className="w-5 h-5 flex-shrink-0" />
                        <span className="hidden md:block font-medium">{item.label}</span>
                        {/* Hover tooltip for mobile could go here */}
                    </NavLink>
                ))}
            </nav>

            <div className="p-4 border-t border-slate-700/50">
                <button onClick={onSettingsClick} className="flex items-center gap-3 px-3 py-3 w-full rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/50 transition-all">
                    <Settings className="w-5 h-5" />
                    <span className="hidden md:block font-medium">Settings</span>
                </button>
            </div>
        </aside>
    );
}
