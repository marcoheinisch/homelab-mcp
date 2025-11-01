FROM python:3.11-slim as base

# Install system dependencies if needed (timezone data, locales, etc.)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY caldav_service.py fastapi_app.py ./

# Expose the port used by uvicorn
EXPOSE 8000

# Default command to run the FastAPI application
CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]