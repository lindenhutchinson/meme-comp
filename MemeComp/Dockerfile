# Use a separate build stage for the Python dependencies and Django app
FROM python:3.10-slim-buster as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code
WORKDIR /code

ENV ENVIRONMENT=production

COPY .env.prod /code/.env.prod

COPY requirements.txt /code/requirements.txt

RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/ \
    && apt-get purge -y --auto-remove build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /code/

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate
RUN python manage.py migrate app

# Expose the HTTP port
EXPOSE 8000

# Start the Daphne server
CMD ["daphne", "-p", "8000", "-b", "0.0.0.0", "MemeComp.asgi:application"]
