FROM python:3.12-slim

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=240 \
    PIP_PROGRESS_BAR=off

# Mismas dependencias de sistema que plate-service (tambien usa
# opencv-python-headless + ultralytics).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8010

CMD ["python", "garita_controller.py"]
