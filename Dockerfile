FROM python:3.11.3-slim-buster

WORKDIR /app

COPY requirements /app/requirements
RUN python -m pip install --no-cache-dir -r requirements/base.txt

COPY . /app
