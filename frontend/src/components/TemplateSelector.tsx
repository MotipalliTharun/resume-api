import { AVAILABLE_TEMPLATES } from '../types/templates';
import { LayoutTemplate, CheckCircle2 } from 'lucide-react';

interface TemplateSelectorProps {
    selectedId: string;
    onSelect: (id: string) => void;
}

export function TemplateSelector({ selectedId, onSelect }: TemplateSelectorProps) {
    return (
        <div className="bg-white rounded-[2rem] p-8 border border-slate-200 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center text-violet-600">
                    <LayoutTemplate className="w-5 h-5" />
                </div>
                <div>
                    <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">Format Selection</h3>
                    <p className="text-[10px] text-slate-500 font-medium">Choose an ATS-optimized layout.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {AVAILABLE_TEMPLATES.map((t) => {
                    const isActive = selectedId === t.id;
                    return (
                        <button
                            key={t.id}
                            onClick={() => onSelect(t.id)}
                            className={`relative text-left p-4 rounded-xl border-2 transition-all duration-300 group ${isActive ? 'border-violet-600 bg-violet-50/50' : 'border-slate-100 hover:border-violet-200 hover:bg-slate-50'}`}
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className={`text-xs font-black uppercase tracking-widest ${isActive ? 'text-violet-700' : 'text-slate-700'}`}>{t.name}</span>
                                        {isActive && <CheckCircle2 className="w-3 h-3 text-violet-600" />}
                                    </div>
                                    <p className="text-[10px] text-slate-500 mt-1 pr-6 leading-relaxed">{t.description}</p>
                                </div>
                                {/* Mini Preview Mockup */}
                                <div className={`w-16 h-20 rounded border shadow-sm flex flex-col p-1 gap-1 ${t.id === 'executive' ? 'font-serif' : 'font-sans'} ${isActive ? 'bg-white border-violet-100' : 'bg-slate-50 border-slate-200'}`}>
                                    <div className="w-1/2 h-1 bg-slate-300 rounded-full mb-1" />
                                    <div className="w-full h-px bg-slate-200" />
                                    <div className="w-3/4 h-[2px] bg-slate-200 rounded-full" />
                                    <div className="w-full h-[2px] bg-slate-200 rounded-full" />
                                    <div className="w-5/6 h-[2px] bg-slate-200 rounded-full" />
                                </div>
                            </div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
