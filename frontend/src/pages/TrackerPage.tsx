import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Building, Calendar, FileText, Search } from 'lucide-react';

interface RunHistory {
    id: number;
    job_title: string;
    company: string;
    created_at: string;
}

const API_BASE = '/api';

export function TrackerPage() {
    const [history, setHistory] = useState<RunHistory[]>([]);
    const [filter, setFilter] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        fetch(`${API_BASE}/runs`)
            .then(res => res.json())
            .then(data => setHistory(data))
            .catch(err => console.error(err));
    }, []);

    const filteredHistory = history.filter(run =>
        (run.job_title || '').toLowerCase().includes(filter.toLowerCase()) ||
        (run.company || '').toLowerCase().includes(filter.toLowerCase())
    );

    return (
        <div className="w-full max-w-7xl mx-auto px-6 py-10">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-10">
                <div>
                    <h1 className="text-3xl font-black text-slate-900 tracking-tight mb-2">Application Tracker</h1>
                    <p className="text-slate-500 font-medium">Manage and review your targeted resume applications.</p>
                </div>

                <div className="relative w-full md:w-auto min-w-[300px]">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search by company or role..."
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="w-full h-12 pl-12 pr-4 bg-white border border-slate-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium"
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredHistory.map((run) => (
                    <div
                        key={run.id}
                        onClick={() => navigate(`/analysis/${run.id}`)}
                        className="group bg-white rounded-2xl p-6 border border-slate-200 hover:border-blue-500/30 hover:shadow-xl hover:shadow-blue-500/5 transition-all cursor-pointer relative overflow-hidden"
                    >
                        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-blue-500/5 to-transparent rounded-bl-full pointer-events-none group-hover:scale-110 transition-transform" />

                        <div className="relative">
                            <div className="flex items-center justify-between mb-4">
                                <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
                                    <Building className="w-5 h-5" />
                                </div>
                                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 bg-slate-50 px-2 py-1 rounded-lg border border-slate-100">
                                    Applied
                                </span>
                            </div>

                            <h3 className="text-lg font-bold text-slate-900 mb-1 line-clamp-1">{run.company || 'Unknown Company'}</h3>
                            <p className="text-slate-500 font-medium text-sm mb-6 line-clamp-1">{run.job_title || 'Untitled Role'}</p>

                            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                                <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
                                    <Calendar className="w-3.5 h-3.5" />
                                    {new Date(run.created_at).toLocaleDateString()}
                                </div>
                                <div className="flex items-center gap-1 text-blue-600 text-xs font-bold uppercase tracking-wider group-hover:translate-x-1 transition-transform">
                                    Review
                                    <ArrowRight className="w-3.5 h-3.5" />
                                </div>
                            </div>
                        </div>
                    </div>
                ))}

                {filteredHistory.length === 0 && (
                    <div className="col-span-full py-20 flex flex-col items-center justify-center text-slate-400">
                        <FileText className="w-12 h-12 mb-4 opacity-50" />
                        <p className="font-bold">No applications found.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
