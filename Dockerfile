# Python 3.9 tabanlı hafif bir imaj kullanıyoruz
FROM python:3.9-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Sistem bağımlılıklarını yükle (psycopg2 ve lxml için gerekli olabilir)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Gereksinim dosyasını kopyala ve yükle
COPY requirements_soa.txt .
RUN pip install --no-cache-dir -r requirements_soa.txt

# Proje dosyalarını kopyala
COPY . .

# Konteynerın dinleyeceği port (Flask varsayılanı değil, bizim belirlediğimiz port)
EXPOSE 8000

# Uygulamayı başlat
CMD ["python", "real_soap_service.py"]