import asyncio
import json
import difflib
import sys
from typing import Dict, Any, List
from services.ollama_service import ollama_generate
from utils import render_prompt
from config import settings

# Mock Settings for Testing
TEST_MODEL = "llama3.2:1b"
OLLAMA_URL = settings.ollama_base_url

class AIModelTester:
    def __init__(self, model: str = TEST_MODEL):
        self.model = model

    async def test_tailor_resume(self, jd: str, resume: str, missing_keywords: List[str]) -> Dict[str, Any]:
        """
        Tests the tailor_resume.txt prompt.
        """
        print(f"\n--- Testing Prompt: tailor_resume.txt ---")
        prompt = render_prompt("prompts/tailor_resume.txt", 
                               JD_TEXT=jd, 
                               RESUME_TEXT=resume, 
                               MISSING_KEYWORDS=", ".join(missing_keywords))
        
        try:
            output = await ollama_generate(OLLAMA_URL, self.model, prompt)
            
            # Validation Logic
            checks = {
                "Has Summary": "SUMMARY" in output.upper(),
                "Has Skills": "SKILLS" in output.upper(),
                "Has Experience": "EXPERIENCE" in output.upper(),
                "No Hallucinated Company": "FakeCorp" not in output, # Negative check
                "Keyword Inclusion": any(k.lower() in output.lower() for k in missing_keywords)
            }
            
            return {"output": output, "checks": checks}
        except Exception as e:
            return {"error": str(e)}

    async def test_requirements_extraction(self, jd: str) -> Dict[str, Any]:
        """
        Tests the extract_requirements.txt prompt.
        """
        print(f"\n--- Testing Prompt: extract_requirements.txt ---")
        prompt = render_prompt("prompts/extract_requirements.txt", JD_TEXT=jd)
        
        try:
            output = await ollama_generate(OLLAMA_URL, self.model, prompt)
            
            # Try to parse as JSON
            try:
                data = json.loads(output)
                checks = {
                    "Is Valid JSON": True,
                    "Has Role Title": "role_title" in data,
                    "Has Keywords": "keywords" in data and len(data["keywords"]) > 0
                }
                return {"output": data, "checks": checks}
            except:
                return {"output": output, "checks": {"Is Valid JSON": False}, "error": "Output was not valid JSON"}
                
        except Exception as e:
            return {"error": str(e)}

async def run_quality_suite():
    tester = AIModelTester()
    
    # Test Data: Data Scientist
    jd_sample = """
    We are looking for a Data Scientist with 3+ years of experience in Python, SQL, and AWS. 
    Experience with PyTorch or TensorFlow for deep learning is a plus. 
    Responsibilities include building predictive models and automating data pipelines.
    """
    resume_sample = """
    John Doe
    Software Engineer with experience in Python and SQL. 
    Built a data ingestion tool at PreviousCompany using Python. 
    Education: BS in CS.
    """
    missing_kws = ["AWS", "PyTorch", "Predictive Modeling"]

    # 1. Tailoring Test
    tailor_result = await tester.test_tailor_resume(jd_sample, resume_sample, missing_kws)
    print(f"Tailoring Result Checks: {tailor_result.get('checks')}")
    if "error" in tailor_result:
        print(f"Error: {tailor_result['error']}")
    else:
        print(f"Sample Output Snippet: {tailor_result['output'][:200]}...")

    # 2. Extraction Test
    extract_result = await tester.test_requirements_extraction(jd_sample)
    print(f"Extraction Result Checks: {extract_result.get('checks')}")
    if "error" in extract_result:
        print(f"Error: {extract_result['error']}")

if __name__ == "__main__":
    asyncio.run(run_quality_suite())
