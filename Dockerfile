FROM python:3.11-slim

LABEL maintainer="Jyotish Dashboard"
LABEL description="Vedic Astrology Kundli Dashboard"

# System deps for pyswisseph + ephem build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make wget curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Download Swiss Ephemeris data files (Moshier — good for 600 BC to 2400 AD)
RUN mkdir -p /app/ephe && \
    wget -q -O /app/ephe/seas_18.se1 \
        https://www.astro.com/ftp/swisseph/ephe/seas_18.se1 || true && \
    wget -q -O /app/ephe/semo_18.se1 \
        https://www.astro.com/ftp/swisseph/ephe/semo_18.se1 || true && \
    wget -q -O /app/ephe/sepl_18.se1 \
        https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1 || true

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Set ephemeris path for pyswisseph
ENV SE_EPHE_PATH=/app/ephe
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

# Use gunicorn in production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--workers", "2", "--threads", "4", \
     "--timeout", "120", \
     "run:app"]
