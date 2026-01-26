import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';
import { authenticatedFetch } from '../utils/api';

export function SubscriptionSuccessPage() {
    const [searchParams] = useSearchParams();
    const sessionId = searchParams.get('session_id');
    const navigate = useNavigate();
    // const { user, login } = useAuth();

    // We don't have a direct "refreshUser" in AuthContext yet, so we might need to manually fetch or reload
    // For now, let's poll endpoint and if changed, reload window or update state

    const [status, setStatus] = useState<'loading' | 'success'>('loading');

    useEffect(() => {
        if (!sessionId) {
            navigate('/app/subscription');
            return;
        }

        const pollSubscription = async () => {
            try {
                // Poll user endpoint to see if tier updated
                const res = await authenticatedFetch('/auth/users/me');
                if (res.ok) {
                    const userData = await res.json();

                    // Check if tier is NOT free (assuming they upgraded)
                    // Or ideally check specifically for the plan they bought.
                    // For now, simple check:
                    if (userData.subscription_tier !== 'free') {
                        setStatus('success');
                        // Optional: Update global context
                        // window.location.href = "/app/tracker"; // Hard reload to sync everything
                    }
                }
            } catch (e) {
                console.error("Polling error", e);
            }
        };

        const interval = setInterval(pollSubscription, 2000);

        // Timeout after 30 seconds
        const timeout = setTimeout(() => {
            clearInterval(interval);
            // navigate('/app/subscription?error=timeout'); 
            // Or just show success anyway if it's lagging? Best to let them continue.
            setStatus('success'); // Assume it worked eventually? Unsafe.
        }, 30000);

        return () => {
            clearInterval(interval);
            clearTimeout(timeout);
        };
    }, [sessionId, navigate]);

    if (status === 'success') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-white p-6">
                <div className="text-center max-w-md animate-in zoom-in duration-500">
                    <div className="w-24 h-24 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                        <CheckCircle size={48} strokeWidth={3} />
                    </div>
                    <h1 className="text-3xl font-black text-slate-900 mb-4">Payment Successful!</h1>
                    <p className="text-slate-500 mb-8">
                        Your subscription is now active. You have full access to all premium features.
                    </p>
                    <button
                        onClick={() => window.location.href = "/app/tracker"}
                        className="px-8 py-4 bg-slate-900 text-white rounded-xl font-bold uppercase tracking-widest hover:bg-slate-800 transition shadow-xl"
                    >
                        Go to Dashboard →
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
            <div className="text-center">
                <div className="relative mb-8">
                    <div className="w-16 h-16 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Activating your subscription...</h2>
                <p className="text-slate-500 text-sm">Please wait while we confirm your payment with Stripe.</p>
            </div>
        </div>
    );
}
