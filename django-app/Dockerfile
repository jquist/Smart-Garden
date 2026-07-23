FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirement.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirement.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && (python manage.py seed --skip-if-plants-exist &) && gunicorn Plant_plotter_settings.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 180"]
