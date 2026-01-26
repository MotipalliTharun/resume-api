import { Check, Shield } from 'lucide-react';

const PlanCard = ({
    name,
    price,
    features,
    recommended = false,
    onSelect
}: {
    name: string;
    price: string;
    features: string[];
    recommended?: boolean;
    onSelect: () => void;
}) => (
    <div className={`relative p-8 rounded-[2.5rem] border transition-all duration-300 ${recommended
        ? 'bg-gradient-to-b from-slate-900 to-slate-800 text-white border-transparent shadow-xl scale-105 z-10'
        : 'bg-white border-slate-200 text-slate-900 hover:border-violet-200 hover:shadow-lg'
        }`}>
        {recommended && (
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-violet-600 to-indigo-600 text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-lg shadow-violet-500/30">
                MOST POPULAR
            </div>
        )}

        <div className="mb-8">
            <h3 className={`text-lg font-bold mb-2 ${recommended ? 'text-slate-200' : 'text-slate-600'}`}>{name}</h3>
            <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold tracking-tight">{price}</span>
                <span className={`text-sm ${recommended ? 'text-slate-400' : 'text-slate-500'}`}>/month</span>
            </div>
        </div>

        <ul className="space-y-4 mb-8">
            {features.map((feat, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                    <div className={`mt-0.5 p-0.5 rounded-full ${recommended ? 'bg-violet-500/20 text-violet-300' : 'bg-violet-100 text-violet-600'}`}>
                        <Check size={12} strokeWidth={3} />
                    </div>
                    <span className={recommended ? 'text-slate-300' : 'text-slate-600'}>{feat}</span>
                </li>
            ))}
        </ul>

        <button
            onClick={onSelect}
            className={`w-full py-4 rounded-xl font-bold transition-all ${recommended
                ? 'bg-white text-slate-900 hover:bg-slate-100'
                : 'bg-slate-900 text-white hover:bg-slate-800'
                }`}
        >
            Choose {name}
        </button>
    </div>
);

export const SubscriptionPage = () => {
    // const { user } = useAuth();

    const handleSubscribe = async (plan: string) => {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch('/api/payment/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ plan_id: plan.toLowerCase() })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Payment initialization failed');
            }

            const data = await response.json();
            if (data.url) {
                window.location.href = data.url;
            } else {
                alert('No checkout URL returned');
            }
        } catch (e: any) {
            alert(`Failed to start checkout: ${e.message}`);
        }
    };

    return (
        <div className="min-h-screen bg-mesh p-8 md:p-12 overflow-y-auto custom-scroll">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-16 fade-up">
                    <h1 className="text-4xl md:text-5xl font-bold text-slate-900 font-heading mb-4">
                        Upgrade your Career
                    </h1>
                    <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                        Unlock advanced AI models, unlimited resume tailoring, and premium templates.
                    </p>
                </div>

                <div className="grid md:grid-cols-3 gap-8 items-center fade-up" style={{ animationDelay: '0.1s' }}>

                    <PlanCard
                        name="Starter"
                        price="$0"
                        features={[
                            "3 Resume Tailors per month",
                            "Basic AI Keyword Analysis",
                            "Standard Templates",
                            "Community Support"
                        ]}
                        onSelect={() => handleSubscribe('Free')}
                    />

                    <PlanCard
                        name="Pro"
                        price="$19"
                        recommended={true}
                        features={[
                            "Unlimited Resume Tailoring",
                            "GPT-4o Advanced Analysis",
                            "Cover Letter Generator",
                            "Application Tracker",
                            "Priority Support",
                            "Export to DOCX & PDF"
                        ]}
                        onSelect={() => handleSubscribe('pro')}
                    />

                    <PlanCard
                        name="Naval Ravikant Edition"
                        price="$49"
                        features={[
                            "Everything in Pro",
                            "1-on-1 Career Coaching AI",
                            "LinkedIn Profile Optimization",
                            "Automated Job Applications (Coming Soon)",
                            "API Access"
                        ]}
                        onSelect={() => handleSubscribe('enterprise')}
                    />
                </div>

                <div className="mt-20 fade-up" style={{ animationDelay: '0.2s' }}>
                    <div className="glass-card p-8 md:p-12 flex flex-col md:flex-row items-center gap-8 text-center md:text-left">
                        <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 flex items-center justify-center text-indigo-600 flex-shrink-0">
                            <Shield size={32} />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-xl font-bold text-slate-900 mb-2">Enterprise Security included</h3>
                            <p className="text-slate-600">
                                CluesStack.io is built with SOC2 compliant infrastructure. Your data is encrypted at rest and in transit.
                            </p>
                        </div>
                        <button className="px-8 py-3 rounded-xl border border-slate-200 font-semibold text-slate-600 hover:bg-slate-50 transition-all">
                            Learn more
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
