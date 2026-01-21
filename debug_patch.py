
import sys
import os

# App context
sys.path.append(os.path.abspath("app"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.tailor_service import update_run_text
from models import TailorRun, Base

# Mock DB
# We can't easily connect to the real PG unless we know credentials or if it's running locally accesible.
# Let's try to mock the Run object and Session if possible, OR connect to actual DB if configured.
# Env var DATABASE_URL might be needed.
# For now, let's just mock the 'db' session and 'run' object to test the function logic (path generation, export calls).

class MockRun:
    id = 999
    job_title = "Debug Engineer"
    company = "Debug Corp"
    full_name = "Debug User"
    tailored_text = "FAKE TEXT"
    tailored_md = ""
    tailored_html = ""

class MockSession:
    def commit(self): pass
    def refresh(self, obj): pass
    def add(self, obj): pass

def test_update():
    print("Testing update_run_text...")
    db = MockSession()
    run = MockRun()
    
    # Text with typical sections
    new_text = """
**PERSONAL DETAILS**
John Doe | 123-456-7890 | email@test.com

**SUMMARY**
Experienced debugger.

**SKILLS**
Python, Debugging.

**WORK EXPERIENCE**
**Role**
**Company** | **Loc** | **Jan 2020**
- Did stuff.
"""
    try:
        update_run_text(db, run, new_text)
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_update()
