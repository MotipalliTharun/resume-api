import React, { useState, useRef, useEffect } from 'react';

// --- Types ---
interface ScoreBreakdown {
    keyword_score: number;
    semantic_score: number;
    ats_score: number;
    total_score: number;
    missing_keywords: string[];
    matched_keywords: string[];
}

interface AnalyzeResponse {
    scores: ScoreBreakdown;
    extracted_keywords: string[];
    jd_top_requirements: string[];
}

interface TailorResponse {
    run_id: number;
    scores: ScoreBreakdown;
    tailored_text: string;
}

const API_BASE = "/api";

export function TailorPage() {
    const [jdText, setJdText] = useState("");
    const [resumeFile, setResumeFile] = useState<File | null>(null);
    const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
    const [tailorResult, setTailorResult] = useState<TailorResponse | null>(null);
    const [isLoading, setIsLoading] = useState<'analyzing' | 'tailoring' | 'saving' | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [fullName, setFullName] = useState(() => localStorage.getItem('fullName') || "Tharun Motipalli");

    const [activeSection, setActiveSection] = useState<'setup' | 'intelligence' | 'draft'>('setup');
    const [isEditing, setIsEditing] = useState(false);
    const [editableText, setEditableText] = useState("");
    const [showComparison, setShowComparison] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);

    // Sync editable text when tailorResult arrives
    useEffect(() => {
        if (tailorResult) {
            setEditableText(tailorResult.tailored_text);
        }
    }, [tailorResult]);

    // Persist name
    useEffect(() => {
        localStorage.setItem('fullName', fullName);
    }, [fullName]);

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files?.[0]) {
            setResumeFile(e.target.files[0]);
            setError(null);
        }
    };

    const handleAnalyze = async () => {
        if (!jdText || !resumeFile) return;
        setIsLoading('analyzing');
        setError(null);
        try {
            const fd = new FormData();
            fd.append("jd_text", jdText);
            fd.append("resume_file", resumeFile);
            const res = await fetch(`${API_BASE}/analyze`, { method: "POST", body: fd });
            if (!res.ok) {
                const text = await res.text();
                throw new Error(text || `Analysis failed (${res.status})`);
            }
            const data = await res.json();
            setAnalysis(data);
            setActiveSection('intelligence');
        } catch (err: any) {
            setError(err.message || "Failed to analyze document.");
        } finally {
            setIsLoading(null);
        }
    };

    const handleTailor = async () => {
        if (!jdText || !resumeFile) return;
        setIsLoading('tailoring');
        setError(null);
        setTailorResult(null);

        try {
            const fd = new FormData();
            fd.append("jd_text", jdText);
            fd.append("resume_file", resumeFile);
            const model = localStorage.getItem('ai_model') || "llama3.2:1b";
            fd.append("model", model);
            fd.append("full_name", fullName);

            const response = await fetch(`${API_BASE}/tailor-stream`, { method: "POST", body: fd });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || `Tailoring failed (${response.status})`);
            }

            if (!response.body) throw new Error("No response body");
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedText = "";

            setTailorResult({
                run_id: 0,
                scores: { keyword_score: 0, semantic_score: 0, ats_score: 0, total_score: 0, missing_keywords: [], matched_keywords: [] },
                tailored_text: ""
            });
            setActiveSection('draft');

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                accumulatedText += chunk;

                const cleanText = accumulatedText.split("---METADATA---")[0];
                setTailorResult(prev => prev ? { ...prev, tailored_text: cleanText } : null);
            }

            if (accumulatedText.includes("---METADATA---")) {
                const parts = accumulatedText.split("---METADATA---");
                const textPart = parts[0].trim();
                const metaPart = parts[1].trim();

                try {
                    const data = JSON.parse(metaPart);
                    setTailorResult({
                        run_id: data.run_id,
                        scores: data.scores,
                        tailored_text: textPart
                    });
                    setAnalysis(prev => prev ? { ...prev, scores: data.scores } : null);
                } catch (e) {
                    console.error("Metadata parsing failed", e);
                }
            }
        } catch (err: any) {
            setError(err.message || "Failed to generate tailored resume.");
        } finally {
            setIsLoading(null);
        }
    };

    const handleSaveEdit = async () => {
        if (!tailorResult || !tailorResult.run_id) {
            setError("Cannot save: Session ID is 0. Please wait for generation to finish or try again.");
            return;
        }
        setIsLoading('saving');
        try {
            const res = await fetch(`${API_BASE}/runs/${tailorResult.run_id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tailored_text: editableText })
            });
            if (!res.ok) throw new Error("Failed to save changes");

            setTailorResult({
                ...tailorResult,
                tailored_text: editableText
            });
            setIsEditing(false);
        } catch (err: any) {
            setError(err.message || "Failed to save edits.");
        } finally {
            setIsLoading(null);
        }
    };

    return (
        <div className="w-full max-w-7xl mx-auto px-6 py-10 pb-32 flex flex-col items-center">
            {/* Header */}
            <div className="w-full flex items-center justify-between mb-10">
                <div>
                    <h1 className="text-3xl font-black text-slate-900 tracking-tight">Tailor Workspace</h1>
                    <p className="text-slate-500 font-bold">New Resume Generation</p>
                </div>

                <div className="flex bg-slate-100 p-1 rounded-2xl border border-slate-200">
                    <SectionToggle
                        label="Setup"
                        active={activeSection === 'setup'}
                        onClick={() => setActiveSection('setup')}
                        icon="1"
                    />
                    <SectionToggle
                        label="Insights"
                        active={activeSection === 'intelligence'}
                        onClick={() => setActiveSection('intelligence')}
                        disabled={!analysis}
                        icon="2"
                    />
                    <SectionToggle
                        label="Draft"
                        active={activeSection === 'draft'}
                        onClick={() => setActiveSection('draft')}
                        disabled={!tailorResult}
                        icon="3"
                    />
                </div>
            </div>

            {error && (
                <div className="fixed top-24 left-1/2 -translate-x-1/2 bg-slate-900 text-white px-6 py-3 rounded-2xl shadow-2xl flex items-center gap-4 z-50 animate-in slide-in-from-top-4 duration-300">
                    <span className="text-rose-400 font-black">!</span>
                    <span className="text-xs font-bold">{error}</span>
                    <button onClick={() => setError(null)} className="ml-4 text-[10px] text-slate-500 hover:text-white uppercase font-black">Close</button>
                </div>
            )}

            {/* SETUP SECTION */}
            {activeSection === 'setup' && (
                <div className="w-full max-w-3xl flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="bg-white rounded-[2rem] p-12 border border-slate-200 shadow-xl">
                        <div className="space-y-8">
                            <div className="space-y-3">
                                <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest">Professional Profile</label>
                                <input
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    placeholder="Full Name (e.g., Tharun Motipalli)"
                                    className="w-full h-16 px-8 rounded-2xl bg-slate-50 border border-slate-100 focus:bg-white focus:border-violet-300 focus:ring-4 focus:ring-violet-50 outline-none transition-all font-bold text-sm"
                                />
                            </div>

                            <div className="space-y-3">
                                <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest">Target Role Specifications</label>
                                <textarea
                                    value={jdText}
                                    onChange={(e) => setJdText(e.target.value)}
                                    placeholder="Paste the job description here..."
                                    className="w-full h-48 px-8 py-6 rounded-[2rem] bg-slate-50 border border-slate-100 focus:bg-white focus:border-cyan-300 focus:ring-4 focus:ring-cyan-50 outline-none transition-all font-medium leading-relaxed custom-scroll text-sm"
                                />
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
                                <div className="space-y-3">
                                    <label className="text-[11px] font-black text-slate-400 uppercase tracking-widest">Base Resume</label>
                                    <div
                                        onClick={() => fileInputRef.current?.click()}
                                        className={`h-40 rounded-[2rem] border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all ${resumeFile ? 'border-emerald-200 bg-emerald-50/30' : 'border-slate-200 hover:border-violet-300 hover:bg-violet-50/30'}`}
                                    >
                                        <input type="file" ref={fileInputRef} hidden onChange={handleFileUpload} />
                                        {resumeFile ? (
                                            <div className="animate-in zoom-in h-full flex flex-col items-center justify-center">
                                                <div className="w-10 h-10 bg-white rounded-xl shadow-sm border border-emerald-100 flex items-center justify-center text-emerald-500 mb-2">✓</div>
                                                <p className="text-xs font-black text-slate-700 truncate px-4 max-w-[200px]">{resumeFile.name}</p>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col items-center">
                                                <div className="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center text-slate-300 mb-2">↑</div>
                                                <p className="text-xs font-bold text-slate-500">Upload PDF/DOCX</p>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="flex flex-col justify-end">
                                    <button
                                        onClick={handleAnalyze}
                                        disabled={!jdText || !resumeFile || !!isLoading}
                                        className="w-full h-20 bg-slate-900 text-white rounded-[2.2rem] font-black uppercase tracking-[0.2em] shadow-xl hover:bg-violet-600 active:scale-95 transition-all disabled:bg-slate-100 disabled:text-slate-300 disabled:shadow-none text-sm"
                                    >
                                        {isLoading === 'analyzing' ? 'Processing...' : 'Initialize Analysis'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* INTELLIGENCE SECTION */}
            {activeSection === 'intelligence' && analysis && (
                <div className="w-full flex flex-col gap-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
                        <BigMetricCard label="ATS Readiness" value={analysis.scores.ats_score} icon="📊" />
                        <BigMetricCard label="Semantic Depth" value={analysis.scores.semantic_score} icon="🧠" />
                        <BigMetricCard label="Skill Coverage" value={analysis.scores.keyword_score} icon="🔑" />
                    </div>

                    <div className="bg-white rounded-[2.5rem] p-12 border border-slate-200 shadow-2xl relative overflow-hidden">
                        <div className="relative">
                            <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-10">
                                <h3 className="text-2xl font-black tracking-tight">Requirement Cross-Mapping</h3>
                                <button
                                    onClick={handleTailor}
                                    disabled={!!isLoading}
                                    className="w-full md:w-auto h-14 px-8 bg-slate-900 text-white rounded-2xl font-black uppercase tracking-widest text-[11px] hover:bg-violet-600 transition-all flex items-center justify-center gap-3 shadow-lg active:scale-95"
                                >
                                    {isLoading === 'tailoring' ? 'Rewriting Experience...' : 'Run Surgical Tailoring'}
                                </button>
                            </div>

                            <div className="flex flex-wrap gap-3">
                                {analysis.extracted_keywords.map((kw, i) => {
                                    const isMissing = analysis.scores.missing_keywords.includes(kw);
                                    return (
                                        <div
                                            key={i}
                                            className={`px-5 py-3 rounded-2xl border text-xs font-bold flex items-center gap-3 transition-all ${isMissing ? 'bg-rose-50 border-rose-100 text-rose-600 shadow-sm' : 'bg-emerald-50 border-emerald-100 text-emerald-600 opacity-60'}`}
                                        >
                                            <div className={`w-2 h-2 rounded-full ${isMissing ? 'bg-rose-400 animate-pulse' : 'bg-emerald-400'}`} />
                                            {kw}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* DRAFT SECTION */}
            {activeSection === 'draft' && (
                <div className="w-full flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500 overflow-visible">
                    <div className="shrink-0 flex items-center justify-between bg-white px-8 py-5 rounded-3xl border border-slate-200 shadow-xl gap-6">
                        <div className="flex items-center gap-8">
                            <div className="flex flex-col">
                                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Doc Status</span>
                                <span className="text-xs font-black text-emerald-500">Verified Precision</span>
                            </div>
                            <div className="h-8 w-px bg-slate-100 hidden md:block" />
                            <div className="flex gap-2">
                                <SectionScore label="ATS" val={tailorResult?.scores.ats_score} />
                                <SectionScore label="CTX" val={tailorResult?.scores.semantic_score} />
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            {isEditing ? (
                                <button
                                    onClick={handleSaveEdit}
                                    disabled={isLoading === 'saving'}
                                    className="h-12 px-6 bg-emerald-500 text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-emerald-600 transition-all shadow-lg active:scale-95 flex items-center justify-center gap-2"
                                >
                                    {isLoading === 'saving' ? 'Committing...' : 'Commit Changes'}
                                </button>
                            ) : (
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="h-12 px-6 bg-slate-900 text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-slate-700 transition-all shadow-lg active:scale-95 flex items-center justify-center gap-2"
                                >
                                    Manual Edit
                                </button>
                            )}

                            <div className="h-8 w-px bg-slate-100" />

                            <div className="flex gap-2">
                                <div className="flex gap-2 relative group">
                                    <button
                                        onClick={() => setShowComparison(!showComparison)}
                                        className={`h-12 w-12 border rounded-xl flex items-center justify-center transition-all shadow-sm ${showComparison ? 'bg-blue-600 text-white border-blue-600' : 'bg-white border-slate-200 text-slate-400 hover:text-blue-600'}`}
                                        title="Compare with Job Description"
                                    >
                                        <span className="text-[14px]">⚖️</span>
                                    </button>

                                    <div className="relative">
                                        <button className="h-12 px-5 bg-slate-900 text-white rounded-xl flex items-center gap-2 hover:bg-slate-700 transition w-full shadow-lg">
                                            <span className="text-[10px] font-black uppercase tracking-widest">Running Export...</span>
                                        </button>
                                        <div className="absolute top-full right-0 mt-3 w-72 bg-white rounded-2xl shadow-2xl border border-slate-100 p-4 z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all transform origin-top-right">
                                            <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-3">Export Configuration</p>
                                            <div className="space-y-3">
                                                <input
                                                    type="text"
                                                    defaultValue={`${fullName.replace(/\s+/g, '_')}_Resume`}
                                                    id="export-filename"
                                                    className="w-full h-10 px-3 text-xs font-bold border rounded-lg bg-slate-50 focus:bg-white focus:ring-2 focus:ring-violet-500 outline-none"
                                                />
                                                <div className="grid grid-cols-2 gap-2">
                                                    <button
                                                        onClick={() => window.open(`${API_BASE}/runs/${tailorResult?.run_id}/download/pdf?name=${(document.getElementById('export-filename') as HTMLInputElement).value}&mode=inline`, '_blank')}
                                                        className="h-10 bg-rose-50 text-rose-600 rounded-lg text-[10px] font-black uppercase hover:bg-rose-100 transition"
                                                    >
                                                        View PDF
                                                    </button>
                                                    <button
                                                        onClick={() => window.open(`${API_BASE}/runs/${tailorResult?.run_id}/download/docx?name=${(document.getElementById('export-filename') as HTMLInputElement).value}`, '_blank')}
                                                        className="h-10 bg-blue-50 text-blue-600 rounded-lg text-[10px] font-black uppercase hover:bg-blue-100 transition"
                                                    >
                                                        DOCX
                                                    </button>
                                                    <button
                                                        onClick={() => window.open(`${API_BASE}/runs/${tailorResult?.run_id}/download/txt?name=${(document.getElementById('export-filename') as HTMLInputElement).value}`, '_blank')}
                                                        className="h-10 bg-slate-50 text-slate-600 rounded-lg text-[10px] font-black uppercase hover:bg-slate-100 transition col-span-2"
                                                    >
                                                        Download TXT
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                        <button className="h-12 w-full absolute top-0 left-0 bg-slate-900 text-white rounded-xl flex items-center justify-center gap-2 shadow-lg group-hover:invisible">
                                            <span className="text-[10px] font-black uppercase tracking-widest">Export Options</span>
                                            <span className="text-xs">↓</span>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 w-full gap-6 flex">
                        {showComparison && (
                            <div className="flex-1 bg-slate-100 rounded-[3rem] border border-slate-200 shadow-inner overflow-hidden flex flex-col min-h-[600px] animate-in slide-in-from-left-4 duration-500">
                                <div className="h-12 shrink-0 flex items-center gap-4 px-8 border-b border-slate-200 bg-slate-200/50">
                                    <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Target Job Description</span>
                                </div>
                                <div className="flex-1 p-8 overflow-y-auto font-sans text-xs leading-relaxed text-slate-600 whitespace-pre-wrap">
                                    {jdText}
                                </div>
                            </div>
                        )}

                        <div className="flex-1 bg-white rounded-[3rem] border border-slate-200 shadow-2xl overflow-hidden flex flex-col min-h-[600px] transition-all duration-500">
                            <div className="h-12 shrink-0 flex items-center gap-4 px-8 border-b border-slate-50 bg-slate-50/20">
                                <div className="flex gap-1.5">
                                    <div className="w-1.5 h-1.5 rounded-full bg-rose-300" />
                                    <div className="w-1.5 h-1.5 rounded-full bg-amber-300" />
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-300" />
                                </div>
                                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest truncate">{fullName}.resume_{isEditing ? 'edit' : 'preview'}</span>
                            </div>

                            <div className="flex-1 p-12 overflow-y-auto no-scrollbar">
                                {isEditing ? (
                                    <textarea
                                        value={editableText}
                                        onChange={(e) => setEditableText(e.target.value)}
                                        className="w-full h-full min-h-[600px] outline-none font-mono text-xs leading-relaxed text-slate-700 bg-transparent resize-none"
                                        spellCheck={false}
                                    />
                                ) : (
                                    <div className="max-w-3xl mx-auto">
                                        <div className="whitespace-pre-wrap font-sans text-[11px] md:text-xs leading-relaxed text-slate-700">
                                            {tailorResult?.tailored_text.split(/(\*\*.*?\*\*)/g).map((part, i) => {
                                                if (part.startsWith('**') && part.endsWith('**')) {
                                                    return <strong key={i} className="font-black text-slate-900">{part.slice(2, -2)}</strong>;
                                                }
                                                return part;
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// --- Local Components ---

function SectionToggle({ label, active, onClick, icon, disabled }: any) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`px-6 h-12 rounded-xl flex items-center gap-3 transition-all shrink-0 ${active ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400 hover:text-slate-600'} ${disabled ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}`}
        >
            <div className={`w-5 h-5 flex items-center justify-center font-black rounded-md text-[10px] ${active ? 'bg-violet-100 text-violet-600' : 'bg-slate-100 text-slate-400'}`}>{icon}</div>
            <span className="text-[11px] font-black uppercase tracking-widest whitespace-nowrap">{label}</span>
        </button>
    );
}

function BigMetricCard({ label, value, icon }: any) {
    const p = Math.round(value * 100);
    return (
        <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-xl flex items-center gap-8">
            <div className="w-16 h-16 bg-slate-50 rounded-2xl flex items-center justify-center text-2xl shadow-inner">{icon}</div>
            <div className="flex-1">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{label}</p>
                <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-slate-900">{p}%</span>
                    <div className="h-1 rounded-full overflow-hidden flex-1 bg-slate-100">
                        <div className="h-full bg-violet-600 transition-all duration-1000" style={{ width: `${p}%` }} />
                    </div>
                </div>
            </div>
        </div>
    );
}

function SectionScore({ label, val }: any) {
    const p = Math.round((val || 0) * 100);
    return (
        <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-50 border border-slate-100 rounded-lg">
            <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest">{label}</span>
            <span className="text-[10px] font-black text-violet-600">{p}%</span>
        </div>
    );
}
