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
1. **NO GENERIC SKILLS**: Do NOT include broad terms like "Communication", "Leadership", "Teamwork", "Agile", "Scrum", or "Problem Solving" unless specifically asked as a hard requirement.
2. **HARD TECH ONLY**: Focus strictly on languages, frameworks, cloud services, tools, libraries, protocols, and specific domain terminologies.
3. **CANONICAL NORMALIZATION**: Convert variations to their standard industry format (e.g., "Springboot" -> "Spring Boot", "ReactJS" -> "React", "NodeJS" -> "Node.js", "Aws" -> "AWS").
4. **EXACT PHRASING**: If the JD uses a specific valid term, prefer that (e.g., "AWS Lambda" over just "Lambda").
5. **VERSION SPECIFICITY**: If a version is mentioned (e.g., "Java 17", "Python 3.x"), include it.

**Extract the following:**

1. **High-Value Keywords** (max 35):
   - **Must-Have**: The core stack (e.g., Java, Kubernetes, AWS).
   - **Nice-to-Have**: Bonus tools referenced (e.g., Redis, Terraform).
   - **Domain**: Industry-specific standards or protocols (e.g., REST, gRPC, ISO 27001).
   
2. **Key Responsibilities** (max 6):
   - Only the most critical technical duties (e.g., "Migrate monolith to microservices using Spring Boot").

**Return ONLY valid JSON in this exact format:**
{
  "keywords": ["Spring Boot", "React", ...],
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

async def extract_contact_info_with_ai(openai_api_key: str, openai_model: str, resume_text: str) -> dict:
    """
    Use OpenAI to extract personal contact details from the resume text.
    """
    import httpx
    
    prompt = f"""Analyze the above resume text and extract the candidate's personal contact information.
    
    Return ONLY valid JSON in this exact format:
    {{
      "full_name": "First Last",
      "email": "email@example.com",
      "phone": "(123) 456-7890",
      "linkedin": "linkedin.com/in/...",
      "location": "City, State",
      "portfolio": "github.com/..."
    }}
    
    If a field is missing, return an empty string "". 
    Do NOT invent information.
    
    **Resume Text:**
    {resume_text[:3000]}
    """
    
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": openai_model,
        "messages": [
            {"role": "system", "content": "You are an expert parser. Extract contact info into JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 500
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            
            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
    except Exception as e:
        print(f"AI Contact Extraction Failed: {e}")
        return {}
