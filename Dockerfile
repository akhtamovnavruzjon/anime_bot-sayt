# Python 3.11 versiyasidan foydalanamiz
FROM python:3.11-slim

# Ishchi katalogini belgilaymiz
WORKDIR /app

# Muhit o'zgaruvchilarini sozlaymiz (Python keshlashini o'chirish va loglarni darhol chiqarish)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tizim paketlarini yangilaymiz (Postgres va boshqa kutubxonalar uchun kerakli dasturlar)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Bog'liqliklar ro'yxatini ko'chirib, o'rnatamiz
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Loyiha kodlarini konteyner ichiga ko'chiramiz
COPY . /app/