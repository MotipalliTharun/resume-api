import fitz  # PyMuPDF

async def parse_via_tika(file_bytes: bytes, filename: str) -> str:
    # Renamed arg but keeping signature for compatibility, 
    # though we ignore 'tika_url' arg in main call now.
    # Actually, main.py calls this. expected signature was (url, bytes, filename).
    # I will change signature here and update main.py.
    
    # Simple PyMuPDF extractor
    # auto-detect slightly tricky from bytes, but fitz.open(stream=..., filetype=...) works
    
    ext = filename.split('.')[-1].lower() if '.' in filename else "pdf"
    
    try:
        doc = fitz.open(stream=file_bytes, filetype=ext)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Parse error: {e}")
        return ""
