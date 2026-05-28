# Base image
FROM python:3.14.2-slim

# Set working directory
WORKDIR /app

# Copy dependency file first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run the app
ENTRYPOINT ["python", "api-dep-moniter.py"]