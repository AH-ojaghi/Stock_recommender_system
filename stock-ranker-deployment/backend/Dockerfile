FROM python:3.10-slim

WORKDIR /app

# system deps (برای ساخت پکیج‌های نیازمند کامپایل)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app code (docker-compose mounts app dir as read-only, اما کپی کردن اینجا مفید است برای build مستقل)
COPY app /app/app

EXPOSE 8000

# Use Gunicorn with Uvicorn workers for production
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.api:app", "--bind", "0.0.0.0:8000"]
