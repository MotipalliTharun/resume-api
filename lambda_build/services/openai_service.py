import httpx
import json

async def openai_generate(api_key: str, model: str, prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional resume tailoring assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        raise

async def openai_stream(api_key: str, model: str, prompt: str):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a professional resume tailoring assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "stream": True
    }
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        content = chunk["choices"][0].get("delta", {}).get("content")
                        if content:
                            yield content
                    except:
                        continue
    except Exception as e:
        print(f"Error in OpenAI stream: {e}")
        yield f"\n[Error: {e}]"
