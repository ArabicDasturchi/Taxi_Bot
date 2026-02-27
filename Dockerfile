FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if any are needed for sqlite/tgcrypto
RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "launcher.py"]
