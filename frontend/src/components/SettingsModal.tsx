import { useState, useEffect } from 'react';
import { authenticatedFetch, getOpenAIKey, setOpenAIKey, setAccessToken, clearAccessToken } from '../utils/api';
import { X, Check, Save } from 'lucide-react';

interface SettingsModalProps {
    onClose: () => void;
}

export function SettingsModal({ onClose }: SettingsModalProps) {
    const [accessCode, setAccessCode] = useState("");
    const [openAIKey, setLocalOpenAIKey] = useState(getOpenAIKey() || "");
    const [message, setMessage] = useState<{ text: string, type: 'success' | 'error' } | null>(null);
    const [status, setStatus] = useState<string>("Checking...");

    useEffect(() => {
        // Check current status
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const res = await authenticatedFetch("/auth/verify", { method: "POST" });
            if (res.ok) {
                setStatus("Authenticated");
            } else {
                setStatus("Not Authenticated");
            }
        } catch (e) {
            setStatus("Error");
        }
    };

    const handleSaveKeys = async () => {
        setMessage(null);

        // REQUIRE Access Code to be entered and verified to save changes
        if (!accessCode) {
            setMessage({ text: "Please enter the Access Code to save changes.", type: "error" });
            return;
        }

        try {
            const testHeaders = { "X-Access-Token": accessCode };
            const res = await fetch("/api/auth/verify", { method: "POST", headers: testHeaders });

            if (res.ok) {
                // Verification Successful - Save Settings
                if (openAIKey) {
                    setOpenAIKey(openAIKey);
                } else {
                    localStorage.removeItem('openai_key');
                }

                setAccessToken(accessCode);
                setMessage({ text: "Settings saved successfully!", type: "success" });
                setStatus("Authenticated");
                setAccessCode(""); // Clear for security after use? Or keep to show Auth? Let's clear.
            } else {
                setMessage({ text: "Invalid Access Code. Cannot save changes.", type: "error" });
            }
        } catch (e) {
            setMessage({ text: "Verification failed. Connection error.", type: "error" });
        }
    };

    const handleLogout = () => {
        clearAccessToken();
        window.dispatchEvent(new Event('auth-error')); // Will trigger Layout to show AccessModal
        onClose();
    };

    return (
        <div className="fixed inset-0 z-[110] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
                <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                    <div>
                        <h2 className="text-xl font-black text-slate-900 tracking-tight">Settings</h2>
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Status: <span className={status === "Authenticated" ? "text-emerald-500" : "text-rose-500"}>{status}</span></p>
                    </div>
                    <button onClick={onClose} className="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center hover:bg-rose-50 hover:text-rose-500 transition-colors">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                <div className="p-8 space-y-8 overflow-y-auto">
                    {/* App Access Code */}
                    <div className="space-y-3">
                        <label className="text-xs font-black text-slate-400 uppercase tracking-widest block">Application Access Code</label>
                        <div className="relative">
                            <input
                                type="password"
                                value={accessCode}
                                onChange={(e) => setAccessCode(e.target.value)}
                                placeholder={status === "Authenticated" ? "•••••••• (Authenticated)" : "Enter Access Code"}
                                className="w-full h-12 px-4 rounded-xl bg-slate-50 border border-slate-200 focus:bg-white focus:border-violet-500 focus:ring-4 focus:ring-violet-50 outline-none transition-all font-bold text-sm"
                            />
                            {status === "Authenticated" && !accessCode && (
                                <div className="absolute right-4 top-1/2 -translate-y-1/2 text-emerald-500">
                                    <Check className="w-4 h-4" />
                                </div>
                            )}
                        </div>
                        <p className="text-[10px] text-slate-400 leading-relaxed">
                            This code is required to access the server. It verifies your session against the server's bcrypt hash.
                        </p>
                    </div>

                    {/* OpenAI API Key */}
                    <div className="space-y-3">
                        <label className="text-xs font-black text-slate-400 uppercase tracking-widest block">OpenAI API Key (Optional)</label>
                        <input
                            type="password"
                            value={openAIKey}
                            onChange={(e) => setLocalOpenAIKey(e.target.value)}
                            placeholder="sk-..."
                            className="w-full h-12 px-4 rounded-xl bg-slate-50 border border-slate-200 focus:bg-white focus:border-cyan-500 focus:ring-4 focus:ring-cyan-50 outline-none transition-all font-mono text-sm"
                        />
                        <p className="text-[10px] text-slate-400 leading-relaxed">
                            Leave blank to use the server's default API key. Providing a key here will override the server setting for your requests.
                        </p>
                    </div>

                    {message && (
                        <div className={`p-4 rounded-xl text-xs font-bold flex items-center gap-2 ${message.type === 'success' ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                            {message.type === 'success' ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                            {message.text}
                        </div>
                    )}
                </div>

                <div className="p-6 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between">
                    <button
                        onClick={handleLogout}
                        className="px-6 py-3 rounded-xl bg-white border border-rose-200 text-rose-600 font-bold text-xs uppercase tracking-widest hover:bg-rose-50 transition-colors"
                    >
                        Disconnect
                    </button>
                    <button
                        onClick={handleSaveKeys}
                        className="px-6 py-3 rounded-xl bg-slate-900 text-white font-bold text-xs uppercase tracking-widest hover:bg-slate-700 transition-colors shadow-lg active:scale-95 flex items-center gap-2"
                    >
                        <Save className="w-4 h-4" />
                        Save Changes
                    </button>
                </div>
            </div>
        </div>
    );
}
