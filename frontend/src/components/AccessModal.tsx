import React, { useState } from 'react';
import { authenticatedFetch, setAccessToken } from '../utils/api';

interface AccessModalProps {
    onSuccess: () => void;
}

export function AccessModal({ onSuccess }: AccessModalProps) {
    const [code, setCode] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            // First set the token temporarily to test it
            setAccessToken(code);
            const res = await authenticatedFetch("/auth/verify", {
                method: "POST",
                // Manually add header here since we just set it in localstorage, 
                // but authenticatedFetch reads from localStorage so it should work.
            });

            if (res.ok) {
                onSuccess();
            } else {
                throw new Error("Invalid Access Code");
            }
        } catch (err) {
            setError("Access verification failed. Incorrect code.");
            localStorage.removeItem('access_token');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/80 backdrop-blur-sm animate-in fade-in duration-300">
            <div className="bg-white p-8 rounded-[2rem] shadow-2xl w-full max-w-md border border-slate-200">
                <div className="flex flex-col items-center mb-6">
                    <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center text-3xl mb-4">
                        🔒
                    </div>
                    <h2 className="text-2xl font-black text-slate-900">Secure Access</h2>
                    <p className="text-slate-500 font-medium text-center mt-2">
                        Please enter the server access code to continue.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        type="password"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        placeholder="Enter Access Code"
                        className="w-full h-14 px-6 rounded-xl bg-slate-50 border border-slate-200 focus:bg-white focus:border-violet-500 focus:ring-4 focus:ring-violet-50 outline-none transition-all font-bold text-center text-lg tracking-widest"
                        autoFocus
                    />

                    {error && (
                        <p className="text-rose-500 text-xs font-black text-center uppercase tracking-wide animate-pulse">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        disabled={!code || loading}
                        className="w-full h-14 bg-slate-900 text-white rounded-xl font-black uppercase tracking-widest hover:bg-violet-600 active:scale-95 transition-all text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? "Verifying..." : "Unlock System"}
                    </button>
                </form>
            </div>
        </div>
    );
}
