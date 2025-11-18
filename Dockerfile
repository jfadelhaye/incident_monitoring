# Use a small Python base image
FROM python:3.12-slim

# Don't write .pyc files, and unbuffer stdout (nice for logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our app code
COPY app.py .

# Expose Flask port
EXPOSE 5000

# Default command: run the Flask app
CMD ["python", "app.py"]

