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

# Production : pas de seed. RUN_SEED_DEMO=1 uniquement en démo locale.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && if [ \"$RUN_SEED_DEMO\" = \"1\" ]; then python manage.py seed_demo; fi && python manage.py runserver 0.0.0.0:8000"]
