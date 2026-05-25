# syntax=docker/dockerfile:1.6
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	PORT=8501

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		libfreetype6 \
		libpng16-16 \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
	&& pip install -r requirements.txt

COPY . .

RUN useradd --create-home --uid 10001 appuser \
	&& chown -R appuser:appuser /app
USER appuser

EXPOSE 8501
CMD ["sh", "-c", "streamlit run ui.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]
