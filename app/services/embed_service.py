from openai import AsyncOpenAI
from config import settings
import numpy as np

client = AsyncOpenAI(api_key=settings.openai_api_key)

async def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    
    # Sanitize input
    valid_texts = [t.replace("\n", " ") for t in texts]
    
    resp = await client.embeddings.create(
        input=valid_texts,
        model="text-embedding-3-small"
    )
    return [d.embedding for d in resp.data]

def cosine_sim(a: list[float], b: list[float]) -> float:
    # dot product / (norm(a)*norm(b))
    if not a or not b: return 0.0
    
    v_a = np.array(a)
    v_b = np.array(b)
    
    norm_a = np.linalg.norm(v_a)
    norm_b = np.linalg.norm(v_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return float(np.dot(v_a, v_b) / (norm_a * norm_b))
