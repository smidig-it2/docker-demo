# Lett baseimage med Python 3.13
FROM python:3.13-slim

# Unngå .pyc/.pyo og __pycache__, og vis logger umiddelbart i konsollen
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Arbeidsmappe i container
WORKDIR /app

# Installer avhengigheter først for god cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopier resten av prosjektet inn
COPY . .

# Appen lytter på 5000
EXPOSE 5000

# Start programmet
CMD ["python", "app.py"]

# Smidig IT-2 © TIP AS, 2026 
