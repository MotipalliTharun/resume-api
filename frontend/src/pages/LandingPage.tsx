import React from 'react';
import { Link } from 'react-router-dom';
import { Check, Shield, Zap, LayoutDashboard, FileText, BarChart3, Star, ArrowRight, MousePointer2, Upload } from 'lucide-react';

const FeatureCard = ({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) => (
    <div className="p-8 rounded-[2rem] bg-white border border-slate-100 shadow-xl shadow-slate-200/50 hover:shadow-2xl hover:border-violet-100 transition-all duration-300 group">
        <div className="w-14 h-14 rounded-2xl bg-slate-50 flex items-center justify-center text-slate-400 group-hover:bg-violet-600 group-hover:text-white transition-all mb-6">
            {icon}
        </div>
        <h3 className="text-xl font-bold text-slate-900 mb-3">{title}</h3>
        <p className="text-slate-500 leading-relaxed text-sm">{desc}</p>
    </div>
);

const PricingCard = ({
    name,
    price,
    features,
    recommended = false
}: {
    name: string,
    price: string,
    features: string[],
    recommended?: boolean
}) => (
    <div className={`relative p-8 rounded-[2.5rem] border transition-all duration-300 flex flex-col h-full ${recommended
        ? 'bg-slate-900 text-white border-transparent shadow-2xl scale-105 z-10'
        : 'bg-white border-slate-200 text-slate-900 hover:border-violet-200 hover:shadow-xl'
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

        <ul className="space-y-4 mb-8 flex-1">
            {features.map((feat, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                    <div className={`mt-0.5 p-0.5 rounded-full ${recommended ? 'bg-violet-500/20 text-violet-300' : 'bg-violet-100 text-violet-600'}`}>
                        <Check size={12} strokeWidth={3} />
                    </div>
                    <span className={recommended ? 'text-slate-300' : 'text-slate-600'}>{feat}</span>
                </li>
            ))}
        </ul>

        <Link
            to="/signup"
            className={`w-full py-4 rounded-xl font-bold transition-all text-center block ${recommended
                ? 'bg-white text-slate-900 hover:bg-slate-100'
                : 'bg-slate-900 text-white hover:bg-slate-800'
                }`}
        >
            Get Started
        </Link>
    </div>
);

const Step = ({ number, title, desc, icon }: { number: string, title: string, desc: string, icon: any }) => (
    <div className="flex flex-col items-center text-center relative z-10">
        <div className="w-16 h-16 rounded-full bg-white border border-slate-200 shadow-xl flex items-center justify-center text-violet-600 mb-6 relative">
            {icon}
            <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center text-sm font-bold border-4 border-slate-50">
                {number}
            </div>
        </div>
        <h3 className="text-xl font-bold text-slate-900 mb-2">{title}</h3>
        <p className="text-slate-500 text-sm max-w-xs">{desc}</p>
    </div>
);

export const LandingPage = () => {
    return (
        <div className="min-h-screen bg-slate-50/50 font-sans selection:bg-violet-200 selection:text-violet-900 overflow-x-hidden">

            {/* Navbar */}
            <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-violet-500/20">
                            C
                        </div>
                        <span className="font-bold text-xl tracking-tight text-slate-900">CluesStack.io</span>
                    </div>
                    <div className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-600">
                        <a href="#how-it-works" className="hover:text-violet-600 transition-colors">How it Works</a>
                        <a href="#features" className="hover:text-violet-600 transition-colors">Features</a>
                        <a href="#pricing" className="hover:text-violet-600 transition-colors">Pricing</a>
                        <Link to="/login" className="hover:text-violet-600 transition-colors">Sign In</Link>
                        <Link to="/signup" className="px-5 py-2.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors shadow-lg shadow-slate-900/10">
                            Get Started
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-40 pb-20 px-6 relative overflow-hidden bg-white">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-full opacity-40 pointer-events-none">
                    <div className="absolute top-[-10%] left-[-10%] w-[40rem] h-[40rem] bg-violet-100 rounded-full mix-blend-multiply filter blur-3xl opacity-70"></div>
                    <div className="absolute top-[-10%] right-[-10%] w-[40rem] h-[40rem] bg-indigo-100 rounded-full mix-blend-multiply filter blur-3xl opacity-70"></div>
                </div>

                <div className="max-w-5xl mx-auto text-center relative z-10 fade-up">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-50 border border-slate-200 text-slate-600 text-xs font-bold uppercase tracking-widest mb-8 shadow-sm">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        <span>Now with GPT-4o Integration</span>
                    </div>
                    <h1 className="text-6xl md:text-8xl font-black text-slate-900 tracking-tighter leading-[1] mb-8 font-heading">
                        Your Resume, <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-indigo-600">Perfected by AI.</span>
                    </h1>
                    <p className="text-xl md:text-2xl text-slate-600 mb-12 max-w-2xl mx-auto leading-relaxed font-medium">
                        Stop guessing keywords. CluesStack tailors your resume to every job description instantly, helping you land 3x more interviews.
                    </p>
                    <div className="flex flex-col md:flex-row items-center justify-center gap-4 mb-20">
                        <Link to="/signup" className="w-full md:w-auto h-14 px-8 bg-slate-900 text-white rounded-2xl font-bold text-lg hover:bg-slate-800 transition-all shadow-xl shadow-slate-900/20 flex items-center justify-center gap-2 hover:-translate-y-1">
                            Start Tailoring Free <ArrowRight size={20} />
                        </Link>
                        <Link to="/login" className="w-full md:w-auto h-14 px-8 bg-white text-slate-600 border border-slate-200 rounded-2xl font-bold text-lg hover:bg-slate-50 transition-all flex items-center justify-center hover:-translate-y-1">
                            See Example
                        </Link>
                    </div>

                    <div className="pt-8 border-t border-slate-100">
                        <p className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Trusted by job seekers at</p>
                        <div className="flex flex-wrap justify-center gap-8 md:gap-16 opacity-40 grayscale">
                            {/* Simple text logos for demo */}
                            <span className="text-xl font-black text-slate-800">Google</span>
                            <span className="text-xl font-black text-slate-800">Amazon</span>
                            <span className="text-xl font-black text-slate-800">Netflix</span>
                            <span className="text-xl font-black text-slate-800">Microsoft</span>
                            <span className="text-xl font-black text-slate-800">Airbnb</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* How It Works */}
            <section id="how-it-works" className="py-24 px-6 bg-slate-50 relative overflow-hidden">
                {/* Connection Line */}
                <div className="hidden md:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-full w-2/3 h-1 bg-gradient-to-r from-transparent via-violet-200 to-transparent z-0"></div>

                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-20">
                        <h2 className="text-3xl md:text-4xl font-black text-slate-900 mb-4">How CluesStack Works</h2>
                        <p className="text-lg text-slate-500">Three simple steps to your dream job.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-12 relative">
                        <Step
                            number="1"
                            title="Upload Resume"
                            desc="Upload your existing PDF or DOCX resume. We verify it matches ATS standards securely."
                            icon={<Upload size={28} />}
                        />
                        <Step
                            number="2"
                            title="Paste Job Description"
                            desc="Copy the job description you want to apply for. Our AI analyzes keywords and requirements."
                            icon={<FileText size={28} />}
                        />
                        <Step
                            number="3"
                            title="Get Tailored PDF"
                            desc="Instantly download a perfectly optimized version of your resume that beats the bots."
                            icon={<MousePointer2 size={28} />}
                        />
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section id="features" className="py-24 px-6 bg-white">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-20">
                        <h2 className="text-3xl md:text-5xl font-black text-slate-900 mb-6 font-heading">Everything you need to win.</h2>
                        <p className="text-lg text-slate-500 max-w-2xl mx-auto">
                            Powerful tools designed to optimize every stage of your job application process.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        <FeatureCard
                            icon={<Zap />}
                            title="Instant Tailoring"
                            desc="Paste a job description and get a perfectly matched resume in seconds. Our AI highlights exactly what recruiters are looking for."
                        />
                        <FeatureCard
                            icon={<FileText />}
                            title="ATS Optimization"
                            desc="Built-in ATS simulator ensures your resume gets past the bots. We verify keyword density, formatting, and semantic matching."
                        />
                        <FeatureCard
                            icon={<LayoutDashboard />}
                            title="Application Tracker"
                            desc="Keep track of every application in one place. Monitor statuses, set reminders, and never miss a follow-up."
                        />
                        <FeatureCard
                            icon={<BarChart3 />}
                            title="Compatibility Score"
                            desc="Get a detailed breakdown of how well you match the role before you apply. Eliminate guesswork."
                        />
                        <FeatureCard
                            icon={<Shield />}
                            title="Data Privacy"
                            desc="Your career data is yours. Secure, encrypted, and private. We never share your personal information."
                        />
                        <FeatureCard
                            icon={<Star />}
                            title="Premium Templates"
                            desc="Choose from a library of recruiter-approved templates that look great and read perfectly."
                        />
                    </div>
                </div>
            </section>

            {/* Pricing Section */}
            <section id="pricing" className="py-32 px-6 bg-slate-50 border-t border-slate-100">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-20">
                        <h2 className="text-3xl md:text-5xl font-black text-slate-900 mb-6 font-heading">Simple, transparent pricing.</h2>
                        <p className="text-lg text-slate-500">Start for free, upgrade when you need more power.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto items-center">
                        <PricingCard
                            name="Starter"
                            price="$0"
                            features={[
                                "3 Resume Tailors / mo",
                                "Basic Keyword Analysis",
                                "1 Standard Template",
                                "Community Support"
                            ]}
                        />
                        <PricingCard
                            name="Pro"
                            price="$19"
                            recommended={true}
                            features={[
                                "Unlimited Tailoring",
                                "GPT-4o Deep Analysis",
                                "All Premium Templates",
                                "Cover Letter Generator",
                                "Priority Support"
                            ]}
                        />
                        <PricingCard
                            name="Enterprise"
                            price="$49"
                            features={[
                                "Everything in Pro",
                                "1-on-1 AI Coaching",
                                "LinkedIn Optimization",
                                "API Access",
                                "Custom Branding"
                            ]}
                        />
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="bg-slate-900 text-white pt-20 pb-10 px-6">
                <div className="max-w-7xl mx-auto">
                    <div className="grid md:grid-cols-4 gap-12 mb-16">
                        <div className="col-span-1 md:col-span-1">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center text-white font-bold text-lg">
                                    C
                                </div>
                                <span className="font-bold text-xl tracking-tight">CluesStack.io</span>
                            </div>
                            <p className="text-slate-400 text-sm leading-relaxed mb-6">
                                The AI-powered career assistant that helps you land your dream job faster. Tailor resumes, track applications, and win.
                            </p>
                            <div className="flex gap-4">
                                {/* Social Icons */}
                                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 hover:bg-slate-700 hover:text-white transition-colors cursor-pointer">𝕏</div>
                                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 hover:bg-slate-700 hover:text-white transition-colors cursor-pointer">in</div>
                                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 hover:bg-slate-700 hover:text-white transition-colors cursor-pointer">ig</div>
                            </div>
                        </div>

                        <div>
                            <h4 className="font-bold text-base mb-6">Product</h4>
                            <ul className="space-y-4 text-sm text-slate-400">
                                <li><a href="#" className="hover:text-white transition-colors">Resume Tailor</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Cover Letter Generator</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Application Tracker</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Chrome Extension</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                            </ul>
                        </div>

                        <div>
                            <h4 className="font-bold text-base mb-6">Resources</h4>
                            <ul className="space-y-4 text-sm text-slate-400">
                                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Resume Templates</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Career Advice</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                            </ul>
                        </div>

                        <div>
                            <h4 className="font-bold text-base mb-6">Company</h4>
                            <ul className="space-y-4 text-sm text-slate-400">
                                <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
                                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
                            </ul>
                        </div>
                    </div>

                    <div className="border-t border-slate-800 pt-8 flex flex-col md:flex-row items-center justify-between gap-6">
                        <p className="text-slate-500 text-sm">© 2024 CluesStack.io. All rights reserved.</p>
                        <div className="flex items-center gap-2 text-sm font-bold text-slate-500">
                            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                            <span>All Systems Operational</span>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};
