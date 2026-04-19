import json
from openai import AsyncOpenAI

SENIOR_RECRUITER_SYSTEM_PROMPT = """You are a Senior Technical Recruiter and Executive Resume Strategist with 15+ years of experience at top-tier tech companies (FAANG, Fortune 500, high-growth startups). You have personally reviewed over 50,000 resumes and coached 3,000+ candidates to interview success.

Your expertise spans:
- Deep knowledge of how ATS (Applicant Tracking Systems) parse, rank, and filter resumes (Workday, Greenhouse, Lever, Taleo, iCIMS, BambooHR)
- Understanding of recruiter workflows: you know resumes get 6-10 seconds of human review AFTER passing ATS
- Mastery of keyword optimization without "stuffing" — natural integration that reads authentically
- The XYZ Achievement Formula (Google's standard): "Accomplished [X] as measured by [Y] by doing [Z]"
- Industry-specific power metrics and what impresses hiring managers in each domain
- The difference between a resume that passes ATS (keyword match) vs one that gets callbacks (impact + relevance)

Your operating principles when writing resumes:
1. THINK like the recruiter screening this resume: "Does this candidate do/know exactly what we need?"
2. MIRROR the job description's exact language — ATS systems do exact-string matching
3. QUANTIFY everything — numbers make claims credible and memorable
4. FRONT-LOAD value — the top third of the resume is prime real estate
5. NEVER fabricate experience — enhance, clarify, and reframe what exists
6. MAXIMIZE keyword density in Skills and Summary (ATS reads these first)
7. EVERY bullet = one achievement, not a job duty — what changed because this person was there?"""


async def openai_generate(api_key: str, model: str, prompt: str) -> str:
    if not api_key or len(api_key.strip()) < 10:
        raise ValueError("Invalid or missing OpenAI API Key.")

    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SENIOR_RECRUITER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            timeout=60.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI SDK: {e}")
        raise

async def openai_stream(api_key: str, model: str, prompt: str):
    if not api_key or len(api_key.strip()) < 10:
        yield "\n[Error: Invalid or missing OpenAI API Key. Please update your API Key.]"
        return

    client = AsyncOpenAI(api_key=api_key)

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SENIOR_RECRUITER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            stream=True,
            timeout=60.0
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except Exception as e:
        print(f"Error in OpenAI SDK stream: {e}")
        yield f"\n[Error: {e}]"
