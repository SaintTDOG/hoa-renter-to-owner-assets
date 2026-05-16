FROM python:3.11-slim

WORKDIR /app

# Install lxml build deps (slim image needs these)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "real_estate_scraper.api:app", "--host", "0.0.0.0", "--port", "8000"]
