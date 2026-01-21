# Resume AI Tailor

A powerful, containerized SaaS application that uses AI to surgically tailor resumes to specific job descriptions. It optimizes for ATS (Applicant Tracking Systems), ensures keyword matching, and generates professional, perfectly formatted PDF resumes.

## 🚀 Features

- **AI-Powered Tailoring**: Uses OpenAI (GPT-4o/mini) to rewrite resume summaries and work experience to match target job requirements.
- **ATS Optimization**: Automatically formats resumes with ATS-friendly layouts, fonts (Times New Roman), and structures.
- **Smart Keyword Extraction**: Identifies critical hard and soft skills from the Job Description and seamlessly integrates them.
- **Live Preview & Editing**: View the generated resume side-by-side with the JD, and make manual edits before finalizing.
- **Instant PDF Generation**: High-quality PDF export using WeasyPrint.
- **Local Overwrite Mode**: Automatically saves the latest tailored resume as `{Full_Name}_Resume.pdf` locally, preventing file clutter.
- **Inline Viewing**: Open generated PDFs directly in the browser instead of downloading duplicate files.
- **Dockerized Architecture**: Complete stack (Frontend, Backend, DB) fully containerized for easy deployment.

## 🛠️ Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Backend**: Python, FastAPI, SQLAlchemy
- **AI Engine**: OpenAI API
- **PDF Engine**: WeasyPrint
- **Database**: PostgreSQL (via Docker)
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

- **Docker Desktop** installed and running.
- An **OpenAI API Key**.

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone <repository_url>
cd Resume-pipeline
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory (or use `.env.example` as a template):

```ini
# .env
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 3. Build and Run with Docker
Start the entire application stack with a single command:

```bash
docker compose up --build -d
```

This will spin up:
- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **Database**: PostgreSQL on port `5432`

## 💡 How to Use

1.  **Open the App**: Navigate to [http://localhost:5173](http://localhost:5173).
2.  **Setup**:
    *   Enter your **Full Name**.
    *   Paste the **Target Job Description** (JD).
    *   Upload your **Base Resume** (PDF/DOCX).
3.  **Analyze**: Click **Initialize Analysis** to let the AI extract keywords and score your resume against the JD.
4.  **Tailor**: Review the insights, then click **Run Surgical Tailoring**.
5.  **Review & Export**:
    *   Edit the generated text if needed.
    *   Click **View PDF** to open the tailored resume in a new tab.
    *   The file is also automatically saved locally as `app/_data/{Your_Name}_Resume.pdf`.

## 📂 Project Structure

```
├── app/                 # Backend (FastAPI)
│   ├── main.py          # API Entrypoint
│   ├── services/        # Logic for AI, Parsing, Rendering
│   ├── templates/       # HTML/Jinja2 Resume Templates
│   └── prompts/         # System Prompts for AI
├── frontend/            # Frontend (React + Vite)
├── docker-compose.yml   # Docker Orchestration
└── requirements.txt     # Python Dependencies
```

## 📝 Customization

- **Prompts**: Edit `app/prompts/tailor_resume.txt` to change how the AI rewrites the resume (e.g., number of bullet points).
- **Templates**: Modify `app/templates/ats_resume.html` to change the styling or layout of the generated PDF.

## 🚀 Deployment

For detailed deployment instructions (Local with Docker Compose or Cloud), please refer to [DEPLOYMENT.md](DEPLOYMENT.md).

## 🐳 Docker Hub Images

The project images are available on Docker Hub:
- Backend: `motipallitharunpf/resume-api:latest`
- Frontend: `motipallitharunpf/resume-ui:latest`
