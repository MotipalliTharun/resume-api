import json
from typing import Optional

async def extract_keywords_with_ai(openai_api_key: str, openai_model: str, jd_text: str) -> dict:
    """
    Use OpenAI to intelligently extract relevant keywords and responsibilities from a Job Description.
    Returns a dict with 'keywords' and 'responsibilities'.
    """
    import httpx
    
    prompt = f"""You are an expert ATS (Applicant Tracking System) analyzer. Analyze the following Job Description and extract ONLY the most critical and relevant information.

**(CRITICAL) SURGICAL EXTRACTION RULES:**
1. **NO GENERIC SKILLS**: Do NOT include broad terms like "Communication", "Leadership", "Teamwork", "Agile", "Scrum", or "Problem Solving" unless specifically asked as a hard requirement certificates.
2. **HARD TECH ONLY**: Focus strictly on languages, frameworks, cloud services, tools, libraries, protocols, and specific domain terminologies (e.g., "GAAP" for finance, "HIPAA" for health).
3. **EXACT PHRASING**: Extract terms exactly as they appear in the JD to ensure high keyword match (e.g., "React.js" vs "React", "AWS Lambda" vs "Lambda").
4. **VERSION SPECIFICITY**: If a version is mentioned (e.g., "Java 17", "Python 3.x"), include it.

**Extract the following:**

1. **High-Value Keywords** (max 35):
   - **Must-Have**: The core stack (e.g., Java, Kubernetes, AWS).
   - **Nice-to-Have**: Bonus tools referenced (e.g., Redis, Terraform).
   - **Domain**: Industry-specific standards or protocols (e.g., REST, gRPC, ISO 27001).
   
2. **Key Responsibilities** (max 6):
   - Only the most critical technical duties (e.g., "Migrate monolith to microservices using Spring Boot").

**Return ONLY valid JSON in this exact format:**
{
  "keywords": ["keyword1", "keyword2", ...],
  "responsibilities": ["resp1", "resp2", ...]
}

**Job Description:**
{jd_text[:4000]}
"""

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": openai_model,
        "messages": [
            {"role": "system", "content": "You are an expert ATS analyzer. Extract ONLY exact, relevant technical keywords. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        content = data["choices"][0]["message"]["content"].strip()
        
        # Parse JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        return result
