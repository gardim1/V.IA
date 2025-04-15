FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y curl gnupg procps && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN ollama pull llama3.2

EXPOSE 8000

CMD bash -c "ollama serve & uvicorn routes.main_api:app --host 0.0.0.0 --port 8000"
