FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for WeasyPrint and PyMuPDF
# libpango-1.0-0, libpangoft2-1.0-0, libharfbuzz-subset0, libjpeg-dev, libopenjp2-7-dev, libffi-dev are common needs
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libreoffice-writer \
    default-jre \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
