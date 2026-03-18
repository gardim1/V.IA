FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade langchain-ollama httpx

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python update_chroma.py && uvicorn routes.main_api:app --host 0.0.0.0 --port ${PORT:-8000}"]
