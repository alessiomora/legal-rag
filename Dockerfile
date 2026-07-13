FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/models/huggingface

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY requirements.txt .
# Install CPU-only PyTorch before sentence-transformers resolves its dependencies.
# This keeps the development image smaller and avoids unnecessary CUDA packages.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY ingestion ./ingestion
COPY evaluation ./evaluation
COPY data ./data
COPY scripts ./scripts
COPY web ./web

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
