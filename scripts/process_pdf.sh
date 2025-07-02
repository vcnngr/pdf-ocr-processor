#!/bin/bash

# Script wrapper per il processore PDF
# Gestisce input/output e validazione

set -e

# Funzione di help
show_help() {
    cat << EOF
PDF OCR Processor - Analizza e ottimizza PDF con OCR

USO:
  docker run --rm -v /path/to/input:/app/input -v /path/to/output:/app/output pdf-ocr-processor <input_file> [output_file]

ESEMPI:
  # Processa documento.pdf e salva come documento_ocr.pdf
  docker run --rm -v \$(pwd):/app/input -v \$(pwd):/app/output pdf-ocr-processor documento.pdf

  # Specifica nome output
  docker run --rm -v \$(pwd):/app/input -v \$(pwd):/app/output pdf-ocr-processor documento.pdf output_personalizzato.pdf

OPZIONI:
  -h, --help     Mostra questo aiuto
  -v, --verbose  Output dettagliato
  -d, --debug    Modalità debug (mantiene file temporanei)

MOUNT POINTS:
  /app/input     Directory con i file PDF di input
  /app/output    Directory per i file processati
EOF
}

# Parsing argomenti
VERBOSE=false
DEBUG=false
INPUT_FILE=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -*)
            echo "Opzione sconosciuta: $1"
            exit 1
            ;;
        *)
            if [ -z "$INPUT_FILE" ]; then
                INPUT_FILE="$1"
            elif [ -z "$OUTPUT_FILE" ]; then
                OUTPUT_FILE="$1"
            else
                echo "Troppi argomenti"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validazione input
if [ -z "$INPUT_FILE" ]; then
    echo "Errore: Specificare file di input"
    show_help
    exit 1
fi

# Se output non specificato, genera automaticamente
if [ -z "$OUTPUT_FILE" ]; then
    filename=$(basename "$INPUT_FILE" .pdf)
    OUTPUT_FILE="${filename}_ocr.pdf"
fi

# Percorsi completi
INPUT_PATH="/app/input/$INPUT_FILE"
OUTPUT_PATH="/app/output/$OUTPUT_FILE"

# Validazione esistenza file
if [ ! -f "$INPUT_PATH" ]; then
    echo "Errore: File di input non trovato: $INPUT_PATH"
    echo "Assicurarsi che il file sia nella directory montata su /app/input"
    exit 1
fi

# Crea directory output se non esistel
mkdir -p /app/output

# Informazioni sul file
echo "=== PDF OCR Processor ==="
echo "File di input: $INPUT_FILE"
echo "File di output: $OUTPUT_FILE"
echo "Dimensione input: $(ls -lh "$INPUT_PATH" | awk '{print $5}')"
echo

# Verifica tipo file
file_type=$(file -b --mime-type "$INPUT_PATH")
if [[ "$file_type" != "application/pdf" ]]; then
    echo "Attenzione: Il file potrebbe non essere un PDF valido (tipo: $file_type)"
fi

# Informazioni aggiuntive se verbose
if [ "$VERBOSE" = true ]; then
    echo "=== Informazioni dettagliate ==="
    echo "Tipo MIME: $file_type"
    echo "Informazioni PDF:"
    pdfinfo "$INPUT_PATH" 2>/dev/null || echo "Impossibile leggere metadati PDF"
    echo
fi

# Esegui il processore Python
echo "Avvio elaborazione..."
start_time=$(date +%s)

if [ "$DEBUG" = true ]; then
    export PYTHONPATH=/app
    python3 /app/pdf_processor.py "$INPUT_PATH" "$OUTPUT_PATH"
else
    python3 /app/pdf_processor.py "$INPUT_PATH" "$OUTPUT_PATH" 2>/dev/null
fi

# Calcola tempo di elaborazione
end_time=$(date +%s)
duration=$((end_time - start_time))

# Risultati finali
if [ -f "$OUTPUT_PATH" ]; then
    echo
    echo "=== Elaborazione completata ==="
    echo "Tempo di elaborazione: ${duration}s"
    echo "File di output: $OUTPUT_FILE"
    echo "Dimensione output: $(ls -lh "$OUTPUT_PATH" | awk '{print $5}')"
    
    # Verifica se il PDF è ricercabile
    echo
    echo "=== Verifica risultato ==="
    if pdfgrep -q "." "$OUTPUT_PATH" 2>/dev/null; then
        echo "✓ PDF risultante è ricercabile"
    else
        echo "⚠ PDF potrebbe non essere ricercabile"
    fi
    
    # Test estrazione testo
    text_chars=$(pdftotext "$OUTPUT_PATH" - 2>/dev/null | wc -c)
    echo "Caratteri di testo estraibili: $text_chars"
    
    if [ "$VERBOSE" = true ]; then
        echo
        echo "=== Metadati PDF finale ==="
        pdfinfo "$OUTPUT_PATH" 2>/dev/null || echo "Impossibile leggere metadati"
    fi
    
    echo
    echo "✓ Processo completato con successo!"
else
    echo
    echo "✗ Errore: File di output non creato"
    exit 1
fi
