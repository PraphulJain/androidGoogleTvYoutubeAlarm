# Use Python Alpine for smallest image size
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install ADB and required system dependencies
# Note: android-tools package provides adb
RUN apk add --no-cache \
    android-tools \
    tzdata \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better layer caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app /app/app

# Set timezone (can be overridden by environment variable)
ENV TZ=UTC

# Expose API port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "app.main"]
