FROM python:3.13-slim

WORKDIR /app

COPY requirments.txt .
RUN pip install --no-cache-dir -r requirments.txt

COPY moniter.py .
COPY api-dep-moniter.py .

ENTRYPOINT ["python", "api-dep-moniter.py"]
