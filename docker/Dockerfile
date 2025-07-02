FROM ubuntu:22.04

# Evita prompts interattivi durante l'installazione
ENV DEBIAN_FRONTEND=noninteractive

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    tesseract-ocr \
    tesseract-ocr-ita \
    tesseract-ocr-eng \
    poppler-utils \
    ghostscript \
    imagemagick \
    qpdf \
    pdfgrep \
    file \
    && rm -rf /var/lib/apt/lists/*

# Configura ImageMagick per permettere operazioni PDF
RUN sed -i 's/^.*policy.*coder.*none.*PDF.*//' /etc/ImageMagick-6/policy.xml

# Copia requirements e installa dipendenze Python
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Crea directory di lavoro
WORKDIR /app

# Copia lo script principale
COPY pdf_processor.py /app/
COPY process_pdf.sh /app/

# Rende eseguibili gli script
RUN chmod +x /app/process_pdf.sh

# Directory per input e output
RUN mkdir -p /app/input /app/output /app/temp

# Comando di default
ENTRYPOINT ["/app/process_pdf.sh"]
