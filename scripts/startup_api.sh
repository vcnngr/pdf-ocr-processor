#!/bin/bash

# Script di avvio per API PDF OCR Processor

set -e

echo "=== PDF OCR Processor API ==="
echo "Avvio in corso..."

# Verifica che Docker sia accessibile
if ! docker info >/dev/null 2>&1; then
    echo "⚠️  Attenzione: Docker non accessibile"
    echo "   Assicurarsi che il socket Docker sia montato:"
    echo "   -v /var/run/docker.sock:/var/run/docker.sock"
fi

# Verifica che l'immagine del processore sia disponibile
if ! docker image inspect pdf-ocr-processor >/dev/null 2>&1; then
    echo "⚠️  Attenzione: Immagine 'pdf-ocr-processor' non trovata"
    echo "   Costruire l'immagine con: docker build -t pdf-ocr-processor ."
fi

# Configurazione Gunicorn
export WORKERS=${WORKERS:-2}
export WORKER_TIMEOUT=${WORKER_TIMEOUT:-600}
export MAX_REQUESTS=${MAX_REQUESTS:-100}
export BIND_ADDRESS=${BIND_ADDRESS:-0.0.0.0:5000}

echo "Configurazione:"
echo "  Workers: $WORKERS"
echo "  Timeout: ${WORKER_TIMEOUT}s"
echo "  Max requests per worker: $MAX_REQUESTS"
echo "  Bind: $BIND_ADDRESS"
echo

# Avvia con Gunicorn per produzione
exec gunicorn \
    --bind "$BIND_ADDRESS" \
    --workers "$WORKERS" \
    --worker-class sync \
    --timeout "$WORKER_TIMEOUT" \
    --max-requests "$MAX_REQUESTS" \
    --max-requests-jitter 10 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    api_wrapper:app
