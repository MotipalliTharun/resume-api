import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Download, FileText, XCircle } from 'lucide-react';


const API_BASE = '/api';

interface ScoreBreakdown {
    keyword_score: number;
    semantic_score: number;
    ats_score: number;
    total_score: number;
    missing_keywords: string[];
    matched_keywords: string[];
}

interface RunDetail {
    id: number;
    full_name: string;
    jd_text: string;
    resume_text: string;
    tailored_text: string;
    scores: ScoreBreakdown;
}

export function AnalysisPage() {
    const { id } = useParams();
    const [run, setRun] = useState<RunDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'diff'>('overview');

    useEffect(() => {
        if (!id) return;
        fetch(`${API_BASE}/runs/${id}`)
            .then(res => res.json())
            .then(data => {
                setRun(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, [id]);

    if (loading) return <div className="flex h-full items-center justify-center font-bold text-slate-400 animate-pulse">Loading analysis...</div>;
    if (!run) return <div className="flex h-full items-center justify-center font-bold text-rose-500">Analysis not found.</div>;

    const { scores } = run;

    return (
        <div className="w-full max-w-7xl mx-auto px-6 py-10 pb-32">
            {/* Header */}
            <div className="flex items-center gap-4 mb-8">
                <Link to="/tracker" className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center hover:bg-slate-50 transition-colors text-slate-500">
                    <ArrowLeft className="w-5 h-5" />
                </Link>
                <div>
                    <h1 className="text-2xl font-black text-slate-900 tracking-tight">Application Analysis</h1>
                    <p className="text-slate-500 text-sm font-medium">Deep dive into tailoring results.</p>
                </div>
                <div className="ml-auto flex gap-2">
                    <a href={`${API_BASE}/runs/${run.id}/download/pdf`} className="px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-2 hover:bg-slate-800 transition-colors">
                        <Download className="w-4 h-4" /> PDF
                    </a>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 bg-slate-100 p-1 rounded-xl mb-8 w-fit">
                <button
                    onClick={() => setActiveTab('overview')}
                    className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${activeTab === 'overview' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`}
                >
                    Score & Skills
                </button>
                <button
                    onClick={() => setActiveTab('diff')}
                    className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${activeTab === 'diff' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`}
                >
                    Resume Comparison
                </button>
            </div>

            {activeTab === 'overview' && (
                <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Scores Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <ScoreCard label="Total Match" value={scores.total_score} color="blue" />
                        <ScoreCard label="Keywords" value={scores.keyword_score} color="emerald" />
                        <ScoreCard label="Semantic" value={scores.semantic_score} color="purple" />
                        <ScoreCard label="ATS Format" value={scores.ats_score} color="amber" />
                    </div>

                    {/* Skill Gap Analysis */}
                    <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-xl">
                        <h2 className="text-xl font-black text-slate-900 mb-6 flex items-center gap-2">
                            <span className="text-2xl">⚡️</span> Skill Gap Analysis
                        </h2>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                            {/* Matches */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between text-xs font-bold uppercase tracking-widest text-emerald-600 border-b border-emerald-100 pb-2">
                                    <span>Matched Skills ({scores.matched_keywords?.length || 0})</span>
                                    <CheckCircle2 className="w-4 h-4" />
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {scores.matched_keywords && scores.matched_keywords.length > 0 ? (
                                        scores.matched_keywords.map((kw, i) => (
                                            <span key={i} className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-bold border border-emerald-100">
                                                {kw}
                                            </span>
                                        ))
                                    ) : (
                                        <span className="text-slate-400 text-sm italic">No direct matches found. Tailor deeper!</span>
                                    )}
                                </div>
                            </div>

                            {/* Gaps */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between text-xs font-bold uppercase tracking-widest text-rose-600 border-b border-rose-100 pb-2">
                                    <span>Missing Skills ({scores.missing_keywords?.length || 0})</span>
                                    <XCircle className="w-4 h-4" />
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {scores.missing_keywords.map((kw, i) => (
                                        <span key={i} className="px-3 py-1.5 bg-rose-50 text-rose-700 rounded-lg text-xs font-bold border border-rose-100">
                                            {kw}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'diff' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[800px] animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Original */}
                    <div className="flex flex-col bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
                        <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-slate-500 text-xs uppercase tracking-widest flex items-center justify-between">
                            <span>Original Resume</span>
                            <FileText className="w-4 h-4" />
                        </div>
                        <div className="flex-1 p-6 overflow-y-auto font-mono text-xs leading-relaxed text-slate-600 whitespace-pre-wrap">
                            {run.resume_text}
                        </div>
                    </div>

                    {/* Tailored */}
                    <div className="flex flex-col bg-white rounded-2xl border border-emerald-100 shadow-xl overflow-hidden ring-4 ring-emerald-50 relative">
                        <div className="absolute top-0 right-0 p-2 z-10">
                            <span className="px-2 py-1 bg-emerald-500 text-white text-[9px] font-black uppercase tracking-widest rounded">Tailored</span>
                        </div>
                        <div className="p-4 bg-emerald-50/50 border-b border-emerald-100 font-bold text-emerald-700 text-xs uppercase tracking-widest flex items-center justify-between">
                            <span>Tailored Output</span>
                            <FileText className="w-4 h-4" />
                        </div>
                        <div className="flex-1 p-6 overflow-y-auto font-sans text-xs leading-relaxed text-slate-800 whitespace-pre-wrap">
                            {run.tailored_text}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function ScoreCard({ label, value, color }: { label: string, value: number, color: string }) {
    const p = Math.round(value * 100);
    const colors: any = {
        blue: 'text-blue-600 bg-blue-50 border-blue-100',
        emerald: 'text-emerald-600 bg-emerald-50 border-emerald-100',
        purple: 'text-purple-600 bg-purple-50 border-purple-100',
        amber: 'text-amber-600 bg-amber-50 border-amber-100'
    };

    return (
        <div className={`p-6 rounded-2xl border ${colors[color]} flex flex-col items-center justify-center gap-2`}>
            <span className="text-4xl font-black">{p}%</span>
            <span className="text-[10px] font-bold uppercase tracking-widest opacity-60">{label}</span>
        </div>
    );
}

