FROM python:3.11-slim AS base

# Install system dependencies if needed (timezone data, locales, etc.)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy application code
COPY . ./

# Expose the port used by uvicorn
EXPOSE 8080
CMD ["uvicorn", "calnode.api:app", "--host", "0.0.0.0", "--port", "8080"]

# add current user to docker group on fedora