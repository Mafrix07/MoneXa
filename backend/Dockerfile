FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=monexa_config.settings

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && if [ \"$RUN_SEED_DEMO\" = \"1\" ]; then python manage.py seed_golden_demo; python manage.py seed_demo; fi && gunicorn monexa_config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
