FROM python:3.11-slim

WORKDIR /app

# curl?????????????????
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# ?root?????????????????
RUN useradd -m -u 1000 appuser

# ????????????root????????
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY llm_app.py .
COPY migration.py .
COPY app/ ./app/
COPY routes/ ./routes/
COPY auth_pkg/ ./auth_pkg/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["python", "app.py"]
hon", "app.py"]
