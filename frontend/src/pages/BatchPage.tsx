import { useState, useRef, useEffect } from 'react';
import { authenticatedFetch } from '../utils/api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface JobEntry {
  id: string;
  job_title: string;
  company: string;
  jd_text: string;
  job_url: string;
  urlScraping: boolean;
  urlError: string | null;
}

interface BatchResult {
  job_title: string;
  company: string;
  run_id: number;
  filename: string;
  total_score: number;
  missing_keywords: string[];
  status: 'success' | 'error';
  error?: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function uid() {
  return Math.random().toString(36).slice(2, 9);
}

function makeEmpty(): JobEntry {
  return { id: uid(), job_title: '', company: '', jd_text: '', job_url: '', urlScraping: false, urlError: null };
}

function scoreColor(score: number) {
  if (score >= 90) return 'text-emerald-600';
  if (score >= 75) return 'text-amber-500';
  return 'text-rose-500';
}

function scoreBadgeBg(score: number) {
  if (score >= 90) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (score >= 75) return 'bg-amber-50 text-amber-700 border-amber-200';
  return 'bg-rose-50 text-rose-700 border-rose-200';
}

function scoreBarColor(score: number) {
  if (score >= 90) return 'bg-emerald-500';
  if (score >= 75) return 'bg-amber-400';
  return 'bg-rose-400';
}

/** Authenticated blob download — works with Bearer token */
async function downloadBlob(url: string, filename: string) {
  const res = await authenticatedFetch(url, { method: 'GET' });
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  const blob = await res.blob();
  const objUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = objUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(objUrl);
}

// ─── JobCard ─────────────────────────────────────────────────────────────────

function JobCard({ job, index, onChange, onRemove, onScrapeUrl }: {
  job: JobEntry;
  index: number;
  onChange: (id: string, field: keyof JobEntry, value: string) => void;
  onRemove: (id: string) => void;
  onScrapeUrl: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header row */}
      <div
        className="flex items-center justify-between px-6 py-4 cursor-pointer hover:bg-slate-50 transition-colors select-none"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-violet-100 text-violet-600 font-black text-xs flex items-center justify-center shrink-0">
            {index + 1}
          </div>
          <div className="min-w-0">
            <p className="font-black text-slate-900 text-sm leading-tight truncate">
              {job.job_title || <span className="text-slate-400">Untitled Role</span>}
            </p>
            <p className="text-[11px] text-slate-400 font-medium leading-tight">
              {job.company || 'No company'} ·{' '}
              {job.jd_text ? `${job.jd_text.length.toLocaleString()} chars` : job.job_url ? 'URL set' : 'No JD yet'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={e => { e.stopPropagation(); onRemove(job.id); }}
            className="w-7 h-7 rounded-lg hover:bg-rose-50 hover:text-rose-500 text-slate-300 flex items-center justify-center text-lg transition-colors"
          >
            ×
          </button>
          <span className="text-slate-300 text-xs">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {/* Body */}
      {expanded && (
        <div className="px-6 pb-6 pt-1 flex flex-col gap-4 border-t border-slate-50">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Job Title *</label>
              <input
                type="text"
                value={job.job_title}
                onChange={e => onChange(job.id, 'job_title', e.target.value)}
                placeholder="e.g. Senior Software Engineer"
                className="h-10 px-4 rounded-xl bg-slate-50 border border-slate-200 text-sm font-medium outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-50 transition-all"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Company</label>
              <input
                type="text"
                value={job.company}
                onChange={e => onChange(job.id, 'company', e.target.value)}
                placeholder="e.g. Google"
                className="h-10 px-4 rounded-xl bg-slate-50 border border-slate-200 text-sm font-medium outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-50 transition-all"
              />
            </div>
          </div>

          {/* URL fetch */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
              Job Posting URL — auto-fetch description
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={job.job_url}
                onChange={e => onChange(job.id, 'job_url', e.target.value)}
                placeholder="https://linkedin.com/jobs/view/..."
                className="flex-1 h-10 px-4 rounded-xl bg-slate-50 border border-slate-200 text-sm font-medium outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-50 transition-all"
              />
              <button
                onClick={() => onScrapeUrl(job.id)}
                disabled={!job.job_url || job.urlScraping}
                className="h-10 px-4 bg-cyan-600 text-white rounded-xl text-[11px] font-black uppercase tracking-widest hover:bg-cyan-700 disabled:bg-slate-100 disabled:text-slate-300 transition-all flex items-center gap-1.5 whitespace-nowrap"
              >
                {job.urlScraping
                  ? <><span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />Fetching</>
                  : 'Fetch JD'}
              </button>
            </div>
            {job.urlError && <p className="text-xs text-rose-500 font-medium">{job.urlError}</p>}
          </div>

          {/* JD paste */}
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                Job Description * (paste or use Fetch JD above)
              </label>
              {job.jd_text && (
                <span className="text-[10px] text-slate-400">{job.jd_text.length.toLocaleString()} chars</span>
              )}
            </div>
            <textarea
              value={job.jd_text}
              onChange={e => onChange(job.id, 'jd_text', e.target.value)}
              placeholder="Paste the full job description here..."
              rows={5}
              className="px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm font-medium outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-50 transition-all resize-y leading-relaxed"
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ─── ResultCard ───────────────────────────────────────────────────────────────

function ResultCard({ result }: { result: BatchResult }) {
  const [downloading, setDownloading] = useState(false);
  const [dlError, setDlError] = useState<string | null>(null);
  const success = result.status === 'success';

  const handleDownload = async () => {
    setDownloading(true);
    setDlError(null);
    try {
      await downloadBlob(
        `/job-ops/download/${encodeURIComponent(result.filename)}`,
        result.filename
      );
    } catch (e: any) {
      setDlError(e.message || 'Download failed');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className={`rounded-3xl border p-5 flex flex-col gap-4 ${success ? 'bg-white border-slate-200 shadow-sm' : 'bg-rose-50 border-rose-200'}`}>
      {/* Top row */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className={`w-10 h-10 rounded-2xl flex items-center justify-center font-black text-sm shrink-0 shadow-sm ${success ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 'bg-rose-100 text-rose-500'}`}>
            {success ? '✓' : '✕'}
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-black text-slate-900 text-sm truncate">{result.job_title || 'Untitled Role'}</p>
            <p className="text-xs text-slate-500 font-medium">{result.company}</p>
          </div>
        </div>

        {/* ATS score badge */}
        {success && (
          <div className={`shrink-0 px-3 py-1.5 rounded-2xl border text-xs font-black ${scoreBadgeBg(result.total_score)}`}>
            ATS {result.total_score.toFixed(1)}%
          </div>
        )}
      </div>

      {/* ATS score bar */}
      {success && (
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-[10px] font-black text-slate-400 uppercase tracking-widest">
            <span>ATS Match Score</span>
            <span className={scoreColor(result.total_score)}>{result.total_score.toFixed(1)}%</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${scoreBarColor(result.total_score)}`}
              style={{ width: `${Math.min(result.total_score, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Missing keywords */}
      {success && result.missing_keywords.length > 0 && (
        <div>
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">
            {result.missing_keywords.length} keywords still missing
          </p>
          <div className="flex flex-wrap gap-1">
            {result.missing_keywords.slice(0, 6).map((kw, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 bg-amber-50 rounded-full text-amber-700 border border-amber-100 font-medium">
                {kw}
              </span>
            ))}
            {result.missing_keywords.length > 6 && (
              <span className="text-[10px] text-slate-400 font-medium">
                +{result.missing_keywords.length - 6} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Error */}
      {!success && (
        <p className="text-xs text-rose-600 font-medium bg-rose-100/50 rounded-xl px-3 py-2">{result.error}</p>
      )}

      {/* DOWNLOAD BUTTON — shows the exact filename so user knows what they're downloading */}
      {success && result.filename && (
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="w-full rounded-2xl bg-slate-900 hover:bg-violet-600 active:scale-[0.98] transition-all shadow-lg disabled:opacity-60 flex flex-col items-center justify-center gap-1 py-3 px-4 group"
        >
          {downloading ? (
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span className="text-white text-xs font-black uppercase tracking-widest">Downloading...</span>
            </div>
          ) : (
            <>
              {/* Icon + label row */}
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-white/80 group-hover:text-white transition-colors" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4" />
                </svg>
                <span className="text-white font-black text-xs uppercase tracking-widest">Download Resume</span>
              </div>
              {/* Filename shown beneath */}
              <span className="text-white/60 text-[10px] font-mono truncate max-w-full group-hover:text-white/80 transition-colors">
                {result.filename}
              </span>
            </>
          )}
        </button>
      )}
      {dlError && <p className="text-xs text-rose-500 font-medium text-center">{dlError}</p>}

      {/* Resume Tailor deep link */}
      {success && result.run_id > 0 && (
        <a
          href={`/app/analysis/${result.run_id}`}
          className="text-center text-[11px] text-violet-600 font-bold hover:underline"
        >
          View full analysis →
        </a>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function BatchPage() {
  const [jobs, setJobs] = useState<JobEntry[]>([makeEmpty()]);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [username, setUsername]   = useState(() => localStorage.getItem('username')    || 'candidate');
  const [fullName, setFullName]   = useState(() => localStorage.getItem('fullName')    || '');
  const [email, setEmail]         = useState(() => localStorage.getItem('b_email')     || '');
  const [phone, setPhone]         = useState(() => localStorage.getItem('b_phone')     || '');
  const [linkedin, setLinkedin]   = useState(() => localStorage.getItem('b_linkedin')  || '');
  const [location, setLocation]   = useState(() => localStorage.getItem('b_location')  || '');
  const [portfolio, setPortfolio] = useState(() => localStorage.getItem('b_portfolio') || '');
  const [showContact, setShowContact] = useState(false);

  const [results, setResults] = useState<BatchResult[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [downloadingAll, setDownloadingAll] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to results once they arrive
  useEffect(() => {
    if (results.length > 0) {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 150);
    }
  }, [results]);

  // ── Job CRUD ────────────────────────────────────────────────────────────────

  const addJob = () => setJobs(prev => [...prev, makeEmpty()]);

  const removeJob = (id: string) =>
    setJobs(prev => prev.length > 1 ? prev.filter(j => j.id !== id) : prev);

  const updateJob = (id: string, field: keyof JobEntry, value: string) =>
    setJobs(prev => prev.map(j => j.id === id ? { ...j, [field]: value } : j));

  const scrapeUrl = async (id: string) => {
    const job = jobs.find(j => j.id === id);
    if (!job?.job_url) return;

    setJobs(prev => prev.map(j => j.id === id ? { ...j, urlScraping: true, urlError: null } : j));

    try {
      const fd = new FormData();
      fd.append('url', job.job_url);
      const res = await authenticatedFetch('/job-ops/scrape-url', { method: 'POST', body: fd });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Scrape failed' }));
        throw new Error(err.detail || 'Scrape failed');
      }

      const data = await res.json();
      setJobs(prev => prev.map(j =>
        j.id === id
          ? { ...j, jd_text: data.jd_text, job_title: j.job_title || data.title || '', urlScraping: false, urlError: null }
          : j
      ));
    } catch (err: any) {
      setJobs(prev => prev.map(j =>
        j.id === id ? { ...j, urlScraping: false, urlError: err.message || 'Scrape failed' } : j
      ));
    }
  };

  // ── Batch Generate ──────────────────────────────────────────────────────────

  const handleGenerate = async () => {
    if (!resumeFile) return setError('Please upload your base resume.');

    const validJobs = jobs.filter(j => j.jd_text.trim() || j.job_url.trim());
    if (validJobs.length === 0) return setError('Add at least one job with a description or URL.');

    setIsGenerating(true);
    setError(null);
    setResults([]);
    setProgress(`Tailoring ${validJobs.length} resume${validJobs.length > 1 ? 's' : ''} — this may take 1-2 min...`);

    try {
      // Persist contact fields so they survive page refresh
      localStorage.setItem('username',    username);
      localStorage.setItem('fullName',    fullName);
      localStorage.setItem('b_email',     email);
      localStorage.setItem('b_phone',     phone);
      localStorage.setItem('b_linkedin',  linkedin);
      localStorage.setItem('b_location',  location);
      localStorage.setItem('b_portfolio', portfolio);

      const fd = new FormData();
      fd.append('resume_file', resumeFile);
      fd.append('jobs_json', JSON.stringify(
        validJobs.map(({ job_title, company, jd_text, job_url }) => ({
          job_title, company, jd_text, job_url: job_url || null,
        }))
      ));
      fd.append('username',  username);
      fd.append('full_name', fullName);
      fd.append('email',     email);
      fd.append('phone',     phone);
      fd.append('linkedin',  linkedin);
      fd.append('location',  location);
      fd.append('portfolio', portfolio);

      const res = await authenticatedFetch('/job-ops/tailor-batch', { method: 'POST', body: fd });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Generation failed' }));
        throw new Error(err.detail || 'Generation failed');
      }

      const data: BatchResult[] = await res.json();
      setResults(data);
      setProgress('');
    } catch (err: any) {
      setError(err.message || 'Batch generation failed.');
      setProgress('');
    } finally {
      setIsGenerating(false);
    }
  };

  // ── ZIP Download ────────────────────────────────────────────────────────────

  const handleDownloadAll = async () => {
    const successResults = results.filter(r => r.status === 'success' && r.filename);
    if (successResults.length === 0) return;

    setDownloadingAll(true);
    try {
      const fd = new FormData();
      fd.append('filenames_json', JSON.stringify(successResults.map(r => r.filename)));
      const res = await authenticatedFetch('/job-ops/download-batch-zip', { method: 'POST', body: fd });
      if (!res.ok) throw new Error('ZIP download failed');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${username}_tailored_resumes.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || 'ZIP download failed.');
    } finally {
      setDownloadingAll(false);
    }
  };

  // ── Computed ────────────────────────────────────────────────────────────────

  const successCount = results.filter(r => r.status === 'success').length;
  const errorCount = results.filter(r => r.status === 'error').length;
  const avgScore = successCount > 0
    ? results.filter(r => r.status === 'success').reduce((a, r) => a + r.total_score, 0) / successCount
    : 0;

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="w-full max-w-4xl mx-auto px-6 py-10 pb-32 flex flex-col gap-8">

      {/* ── Page Header ── */}
      <div>
        <h1 className="text-3xl font-black text-slate-900 tracking-tight">Batch Resume Generator</h1>
        <p className="text-slate-500 font-medium mt-1 text-sm">
          Upload one base resume · add jobs · get a tailored DOCX per job
        </p>
      </div>

      {/* ── Error banner ── */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl px-6 py-4 flex items-center justify-between gap-4">
          <p className="text-rose-700 text-sm font-bold">{error}</p>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-600 font-black text-xl shrink-0">×</button>
        </div>
      )}

      {/* ── Candidate Config ── */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8">
        <h2 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-6">Step 1 — Candidate Info & Base Resume</h2>

        {/* ── Row 1: username + full name ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
              Username <span className="text-slate-300 font-medium normal-case">(used in filename)</span>
            </label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value.replace(/\s/g, '').toLowerCase())}
              placeholder="tharunmotu"
              className="h-11 px-4 rounded-xl bg-slate-50 border border-slate-200 text-sm font-medium outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-50 transition-all"
            />
            <p className="text-[10px] text-slate-400">
              Files: <code className="text-violet-600">{username || 'username'}_job-title_resume.docx</code>
            </p>
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
              Full Name <span className="text-slate-300 font-medium normal-case">(printed on resume)</span>
            </label>
            <input
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              placeholder="Tharun Motipalli"
              className="h-11 px-4 rounded-xl bg-slate-50 border border-slate-200 text-sm font-medium outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-50 transition-all"
            />
          </div>
        </div>

        {/* ── Contact details (collapsible) ── */}
        <div className="mb-6">
          <button
            type="button"
            onClick={() => setShowContact(v => !v)}
            className="flex items-center gap-2 text-[11px] font-black text-slate-500 hover:text-violet-600 uppercase tracking-widest transition-colors"
          >
            <span className={`transition-transform ${showContact ? 'rotate-90' : ''}`}>▶</span>
            Contact Details — phone, email, LinkedIn
            {!email && !phone && (
              <span className="ml-2 px-2 py-0.5 bg-amber-50 text-amber-600 border border-amber-200 rounded-full text-[9px] font-black normal-case tracking-normal">
                Fill in to guarantee contact info on resume
              </span>
            )}
            {(email || phone) && (
              <span className="ml-2 px-2 py-0.5 bg-emerald-50 text-emerald-600 border border-emerald-200 rounded-full text-[9px] font-black normal-case tracking-normal">
                ✓ set
              </span>
            )}
          </button>

          {showContact && (
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { label: 'Email',     value: email,     set: setEmail,     placeholder: 'you@email.com',              type: 'email' },
                { label: 'Phone',     value: phone,     set: setPhone,     placeholder: '+1 (555) 000-0000',          type: 'tel'  },
                { label: 'LinkedIn',  value: linkedin,  set: setLinkedin,  placeholder: 'linkedin.com/in/yourname',   type: 'text' },
                { label: 'Location',  value: location,  set: setLocation,  placeholder: 'City, State',               type: 'text' },
                { label: 'Portfolio', value: portfolio, set: setPortfolio, placeholder: 'github.com/yourname',        type: 'text' },
              ].map(({ label, value, set, placeholder, type }) => (
                <div key={label} className="flex flex-col gap-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{label}</label>
                  <input
                    type={type}
                    value={value}
                    onChange={e => set(e.target.value)}
                    placeholder={placeholder}
                    className="h-10 px-4 rounded-xl bg-slate-50 border border-slate-200 text-sm font-medium outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-50 transition-all"
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Resume upload */}
        <div
          onClick={() => fileInputRef.current?.click()}
          className={`h-28 rounded-2xl border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all ${
            resumeFile
              ? 'border-emerald-300 bg-emerald-50/40'
              : 'border-slate-200 hover:border-violet-300 hover:bg-violet-50/30'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            hidden
            accept=".pdf,.docx,.doc"
            onChange={e => e.target.files?.[0] && setResumeFile(e.target.files[0])}
          />
          {resumeFile ? (
            <div className="flex flex-col items-center gap-1 px-4 text-center">
              <span className="text-2xl">✓</span>
              <p className="text-xs font-black text-emerald-700 truncate max-w-xs">{resumeFile.name}</p>
              <p className="text-[10px] text-slate-400">Click to change file</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-1">
              <span className="text-slate-300 text-3xl">↑</span>
              <p className="text-sm font-bold text-slate-500">Upload your base resume</p>
              <p className="text-[11px] text-slate-400">PDF or DOCX · used for all jobs</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Job List ── */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-black text-slate-400 uppercase tracking-widest">
            Step 2 — Target Jobs ({jobs.length})
          </h2>
          <button
            onClick={addJob}
            className="h-9 px-5 bg-slate-900 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-violet-600 transition-all active:scale-95"
          >
            + Add Job
          </button>
        </div>

        {jobs.map((job, i) => (
          <JobCard
            key={job.id}
            job={job}
            index={i}
            onChange={updateJob}
            onRemove={removeJob}
            onScrapeUrl={scrapeUrl}
          />
        ))}
      </div>

      {/* ── Generate Button ── */}
      <div className="flex flex-col gap-3">
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !resumeFile}
          className="w-full h-16 bg-slate-900 text-white rounded-[2rem] font-black uppercase tracking-[0.15em] hover:bg-violet-600 active:scale-[0.98] transition-all disabled:bg-slate-100 disabled:text-slate-300 shadow-xl flex items-center justify-center gap-3 text-sm"
        >
          {isGenerating ? (
            <>
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              {progress || 'Generating tailored resumes...'}
            </>
          ) : (
            `Step 3 — Generate ${jobs.length} Tailored Resume${jobs.length > 1 ? 's' : ''} ↓`
          )}
        </button>

        {isGenerating && (
          <p className="text-center text-xs text-slate-400 font-medium animate-pulse">
            AI is tailoring each resume to the job description — please wait, do not refresh
          </p>
        )}
      </div>

      {/* ─────────────────────────────────────────────────────────────────────
          RESULTS SECTION — always full width, clearly below the form
      ───────────────────────────────────────────────────────────────────── */}
      {results.length > 0 && (
        <div ref={resultsRef} className="flex flex-col gap-6 scroll-mt-8">

          {/* Results header with stats */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-4 border-t-2 border-slate-100">
            <div>
              <h2 className="text-xl font-black text-slate-900">Your Tailored Resumes</h2>
              <p className="text-sm text-slate-500 font-medium mt-0.5">
                {successCount} generated · {errorCount} failed · avg ATS{' '}
                <span className={`font-black ${scoreColor(avgScore)}`}>{avgScore.toFixed(1)}%</span>
              </p>
            </div>

            {/* Download All ZIP — shown only when 2+ succeeded */}
            {successCount >= 2 && (
              <button
                onClick={handleDownloadAll}
                disabled={downloadingAll}
                className="h-12 px-6 bg-violet-600 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-violet-700 active:scale-95 transition-all shadow-lg disabled:opacity-60 flex items-center gap-2 whitespace-nowrap"
              >
                {downloadingAll
                  ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Zipping...</>
                  : <>↓ Download All ({successCount}) as ZIP</>}
              </button>
            )}
          </div>

          {/* Result cards — full width grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {results.map((result, i) => (
              <ResultCard key={i} result={result} />
            ))}
          </div>

          {/* Bottom download-all again if many results */}
          {successCount >= 3 && (
            <button
              onClick={handleDownloadAll}
              disabled={downloadingAll}
              className="w-full h-14 bg-slate-900 text-white rounded-[2rem] font-black text-sm uppercase tracking-widest hover:bg-violet-600 active:scale-[0.98] transition-all shadow-xl disabled:opacity-60 flex items-center justify-center gap-3"
            >
              {downloadingAll
                ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Building ZIP...</>
                : `↓ Download All ${successCount} Resumes as ZIP`}
            </button>
          )}
        </div>
      )}

      {/* ── How it works ── */}
      {results.length === 0 && !isGenerating && (
        <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">How it works</p>
          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
            {[
              { n: '1', label: 'Upload Resume', desc: 'Your PDF or DOCX base resume' },
              { n: '2', label: 'Add Jobs', desc: 'Paste JDs or drop job URLs to auto-fetch' },
              { n: '3', label: 'Generate', desc: 'AI tailors a resume per job in one pass' },
              { n: '4', label: 'Download', desc: 'Each DOCX appears below with ATS score' },
              { n: '5', label: 'ZIP All', desc: 'Or grab everything as a single ZIP' },
            ].map(step => (
              <div key={step.n} className="flex flex-col items-center text-center gap-2">
                <div className="w-9 h-9 rounded-full bg-violet-100 text-violet-600 font-black text-sm flex items-center justify-center">
                  {step.n}
                </div>
                <p className="text-xs font-black text-slate-700">{step.label}</p>
                <p className="text-[10px] text-slate-400 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
