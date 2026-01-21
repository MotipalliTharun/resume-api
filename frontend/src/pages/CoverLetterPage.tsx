import { useState, useEffect } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, Download, History } from "lucide-react";

interface CoverLetterRun {
    id: number;
    company: string;
    created_at: string;
}

export function CoverLetterPage() {
    const [jdText, setJdText] = useState("");
    const [resumeFile, setResumeFile] = useState<File | null>(null);
    const [jobTitle, setJobTitle] = useState("");
    const [company, setCompany] = useState("");
    const [fullName, setFullName] = useState("");
    const [location, setLocation] = useState("");
    const [phone, setPhone] = useState("");
    const [email, setEmail] = useState("");
    const [linkedin, setLinkedin] = useState("");
    const [portfolio, setPortfolio] = useState("");

    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedText, setGeneratedText] = useState("");
    const [currentRunId, setCurrentRunId] = useState<number | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [history, setHistory] = useState<CoverLetterRun[]>([]);

    useEffect(() => {
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        try {
            const res = await fetch("http://localhost:8000/cover-letters");
            if (res.ok) {
                const data = await res.json();
                setHistory(data);
            }
        } catch (e) {
            console.error("Failed to fetch history", e);
        }
    };

    const handleGenerate = async () => {
        if (!resumeFile || !jdText) {
            setError("Please provide both a Resume and Job Description.");
            return;
        }
        setError(null);
        setIsGenerating(true);
        setGeneratedText("");
        setCurrentRunId(null);

        const formData = new FormData();
        formData.append("jd_text", jdText);
        formData.append("resume_file", resumeFile);
        formData.append("job_title", jobTitle);
        formData.append("company", company);
        formData.append("full_name", fullName);
        formData.append("location", location);
        formData.append("phone", phone);
        formData.append("email", email);
        formData.append("linkedin", linkedin);
        formData.append("portfolio", portfolio);

        try {
            const response = await fetch("http://localhost:8000/cover-letter-stream", {
                method: "POST",
                body: formData,
            });

            if (!response.body) throw new Error("No response body");
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let done = false;

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                const chunkValue = decoder.decode(value, { stream: true });

                // check for metadata
                if (chunkValue.includes("---METADATA---")) {
                    const parts = chunkValue.split("---METADATA---");
                    setGeneratedText((prev) => prev + parts[0]);
                    try {
                        const meta = JSON.parse(parts[1].trim());
                        if (meta.cl_id) {
                            setCurrentRunId(meta.cl_id);
                            fetchHistory();
                        }
                    } catch (e) {
                        console.error("Error parsing metadata", e);
                    }
                } else {
                    setGeneratedText((prev) => prev + chunkValue);
                }
            }

        } catch (err: any) {
            setError(err.message || "Something went wrong generating the cover letter.");
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-8 p-6">
            <div className="flex flex-col md:flex-row gap-8">

                {/* LEFT COLUMN: Inputs */}
                <div className="w-full md:w-1/3 space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                            <Upload className="w-5 h-5 text-indigo-600" />
                            Upload Data
                        </h2>

                        {/* Resume Upload */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Resume (PDF)</label>
                            <div className="relative border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-indigo-500 transition-colors text-center">
                                <input
                                    type="file"
                                    accept=".pdf"
                                    onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                />
                                <div className="space-y-1">
                                    <FileText className="w-8 h-8 mx-auto text-gray-400" />
                                    <p className="text-sm text-gray-600">
                                        {resumeFile ? resumeFile.name : "Click to upload resume"}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* JD Input */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
                            <textarea
                                value={jdText}
                                onChange={(e) => setJdText(e.target.value)}
                                placeholder="Paste the job description here..."
                                rows={6}
                                className="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm p-3 border"
                            />
                        </div>

                        {/* Additional Fields */}
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Full Name</label>
                                <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} className="w-full rounded-md border-gray-300 shadow-sm p-2 border" placeholder="John Doe" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Company Name</label>
                                <input type="text" value={company} onChange={e => setCompany(e.target.value)} className="w-full rounded-md border-gray-300 shadow-sm p-2 border" placeholder="Acme Corp" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Job Title</label>
                                <input type="text" value={jobTitle} onChange={e => setJobTitle(e.target.value)} className="w-full rounded-md border-gray-300 shadow-sm p-2 border" placeholder="Software Engineer" />
                            </div>

                            {/* Contact details (Optional override) */}
                            <details className="text-sm text-gray-500 cursor-pointer">
                                <summary>Contact Details (Optional Override)</summary>
                                <div className="space-y-3 mt-2 pl-2 border-l-2 border-gray-200">
                                    <input type="text" placeholder="Location" value={location} onChange={e => setLocation(e.target.value)} className="w-full rounded-md border p-2" />
                                    <input type="text" placeholder="Phone" value={phone} onChange={e => setPhone(e.target.value)} className="w-full rounded-md border p-2" />
                                    <input type="text" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} className="w-full rounded-md border p-2" />
                                    <input type="text" placeholder="LinkedIn URL" value={linkedin} onChange={e => setLinkedin(e.target.value)} className="w-full rounded-md border p-2" />
                                    <input type="text" placeholder="Portfolio URL" value={portfolio} onChange={e => setPortfolio(e.target.value)} className="w-full rounded-md border p-2" />
                                </div>
                            </details>
                        </div>

                        <button
                            onClick={handleGenerate}
                            disabled={isGenerating || !resumeFile || !jdText}
                            className={`w-full mt-6 flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-white font-medium transition-colors ${isGenerating || !resumeFile || !jdText
                                ? "bg-gray-400 cursor-not-allowed"
                                : "bg-indigo-600 hover:bg-indigo-700 shadow-lg shadow-indigo-200"
                                }`}
                        >
                            {isGenerating ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    <CheckCircle className="w-5 h-5" />
                                    Generate Cover Letter
                                </>
                            )}
                        </button>

                        {error && (
                            <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm flex items-start gap-2">
                                <AlertCircle className="w-5 h-5 shrink-0" />
                                {error}
                            </div>
                        )}
                    </div>

                    {/* HISTORY */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                        <h3 className="text-md font-semibold text-gray-900 mb-3 flex items-center gap-2">
                            <History className="w-4 h-4" /> Recent
                        </h3>
                        <ul className="space-y-2">
                            {history.map((run) => (
                                <li key={run.id} className="text-sm border-b pb-2">
                                    <div className="font-medium text-gray-800">{run.company || "No Company"}</div>
                                    <div className="text-gray-500 text-xs">
                                        {new Date(run.created_at).toLocaleDateString()}
                                        {currentRunId === run.id && <span className="ml-2 text-green-600 font-bold">(New)</span>}
                                    </div>
                                    <a
                                        href={`http://localhost:8000/cover-letters/${run.id}/download/pdf`}
                                        className="text-indigo-600 hover:underline text-xs flex items-center gap-1 mt-1"
                                        target="_blank" rel="noreferrer"
                                    >
                                        <Download className="w-3 h-3" /> PDF
                                    </a>
                                    <a
                                        href={`http://localhost:8000/cover-letters/${run.id}/download/docx`}
                                        className="text-indigo-600 hover:underline text-xs flex items-center gap-1 mt-1"
                                        target="_blank" rel="noreferrer"
                                    >
                                        <Download className="w-3 h-3" /> DOCX
                                    </a>
                                </li>
                            ))}
                            {history.length === 0 && <p className="text-gray-400 text-sm">No history yet.</p>}
                        </ul>
                    </div>

                </div>

                {/* RIGHT COLUMN: Output */}
                <div className="w-full md:w-2/3 space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 min-h-[600px] flex flex-col">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                <FileText className="w-5 h-5 text-indigo-600" />
                                Generated Cover Letter
                            </h2>
                            {currentRunId && (
                                <div className="flex gap-2">
                                    <a
                                        href={`http://localhost:8000/cover-letters/${currentRunId}/download/pdf`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                                    >
                                        <Download className="w-4 h-4" />
                                        PDF
                                    </a>
                                    <a
                                        href={`http://localhost:8000/cover-letters/${currentRunId}/download/docx`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                                    >
                                        <Download className="w-4 h-4" />
                                        DOCX
                                    </a>
                                    <a
                                        href={`http://localhost:8000/cover-letters/${currentRunId}/download/txt`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                                    >
                                        <Download className="w-4 h-4" />
                                        TXT
                                    </a>
                                </div>
                            )}
                        </div>

                        <div className="flex-1 p-6 bg-gray-50 rounded-lg border border-gray-200 font-serif text-gray-800 whitespace-pre-wrap leading-relaxed">
                            {generatedText || <span className="text-gray-400 italic">Generated content will appear here...</span>}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
