import urllib.request
import re
from sqlalchemy import create_engine, text

# Config
API_URL = "http://localhost:8000"
# Use 'db' host if running inside container network, or 'localhost' if port mapped?
# If running 'docker compose exec', we are inside the container provided network?
# 'exec' runs inside the container namespace. So 'localhost:8000' works for the app itself (since we are exec-ing into api container).
# DB_URL needs to point to 'db' host, not localhost, because db is another container.
DB_URL = "postgresql://resume:resume@db:5432/resumeai" 

def verify_filenames():
    try:
        # 1. Get latest Resume Run ID from DB
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # Find a run
            result = conn.execute(text("SELECT id, full_name FROM tailor_runs ORDER BY id DESC LIMIT 1"))
            run = result.fetchone()
            
            if run:
                run_id, full_name = run
                print(f"Checking Resume Run ID: {run_id}, Name: {full_name}")
                
                # Test Download
                url = f"{API_URL}/runs/{run_id}/download/pdf"
                try:
                    with urllib.request.urlopen(url) as response:
                        cd = response.headers.get("Content-Disposition", "")
                        print(f"Resume Content-Disposition: {cd}")
                        # Expected: filename="Tharun_Motipalli_Resume.pdf" (approx)
                        if "_Resume.pdf" in cd:
                            print("✅ Resume filename format correct.")
                        else:
                            print("❌ Resume filename format INCORRECT.")
                except Exception as e:
                     print(f"❌ Failed to download resume: {e}")
            else:
                print("⚠️ No resume runs found to test.")

            # 2. Get latest Cover Letter ID
            result = conn.execute(text("SELECT id, full_name FROM cover_letters ORDER BY id DESC LIMIT 1"))
            cl = result.fetchone()
            
            if cl:
                cl_id, full_name = cl
                print(f"Checking Cover Letter ID: {cl_id}, Name: {full_name}")
                
                # Test Download
                url = f"{API_URL}/cover-letters/{cl_id}/download/pdf"
                try:
                    with urllib.request.urlopen(url) as response:
                        cd = response.headers.get("Content-Disposition", "")
                        print(f"Cover Letter Content-Disposition: {cd}")
                        if "_CoverLetter.pdf" in cd:
                             print("✅ Cover Letter filename format correct.")
                        else:
                             print("❌ Cover Letter filename format INCORRECT.")
                except Exception as e:
                     print(f"❌ Failed to download cover letter: {e}")
            else:
                print("⚠️ No cover letters found to test.")

    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify_filenames()
