FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render/Koyeb/Cloud Run all inject $PORT at runtime; app.py already
# reads it via os.environ.get("PORT", 5000).
ENV PORT=5000
EXPOSE 5000

CMD ["python3", "app.py"]
