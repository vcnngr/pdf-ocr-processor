#!/bin/bash

# PDF OCR Processor - Setup Script
# Crea automaticamente la struttura del progetto

set -e

# Colori per output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 PDF OCR Processor - Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo

# Verifica prerequisiti
echo -e "${BLUE}Verifica prerequisiti...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker non installato${NC}"
    echo "Installa Docker da: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose non installato${NC}"
    echo "Installa Docker Compose da: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker installato: $(docker --version)${NC}"
echo -e "${GREEN}✅ Docker Compose installato: $(docker compose --version)${NC}"

# Crea struttura directory
echo -e "\n${BLUE}Creazione struttura directory...${NC}"

directories=(
    "docker"
    "scripts"
    "examples"
    "config"
    "input"
    "output"
    "batch_input"
    "batch_output"
    "temp"
    "api_temp"
    "logs"
    "backups"
    "tests/sample_files"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    # Crea .gitkeep per directory vuote
    if [ ! "$(ls -A $dir 2>/dev/null)" ]; then
        touch "$dir/.gitkeep"
    fi
    echo -e "${GREEN}  ✅ $dir${NC}"
done

# Copia file dalla root alle directory corrette
echo -e "\n${BLUE}Riorganizzazione file...${NC}"

# Sposta Dockerfile principale
if [ -f "Dockerfile" ] && [ ! -f "docker/Dockerfile" ]; then
    mv Dockerfile docker/
    echo -e "${GREEN}  ✅ Dockerfile → docker/${NC}"
fi

# Sposta docker-compose.yml
if [ -f "docker-compose.yml" ] && [ ! -f "docker/docker-compose.yml" ]; then
    mv docker-compose.yml docker/
    echo -e "${GREEN}  ✅ docker-compose.yml → docker/${NC}"
fi

# Crea symlink per facilità d'uso
if [ ! -f "docker-compose.yml" ] && [ -f "docker/docker-compose.yml" ]; then
    ln -sf docker/docker-compose.yml docker-compose.yml
    echo -e "${GREEN}  ✅ Symlink docker-compose.yml creato${NC}"
fi

# Crea file .env se non esiste
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${GREEN}  ✅ File .env creato da template${NC}"
fi

# Imposta permessi
echo -e "\n${BLUE}Impostazione permessi...${NC}"

# Script eseguibili
find scripts/ -name "*.sh" -exec chmod +x {} \;
if [ -f "Makefile" ]; then
    chmod +x Makefile
fi

echo -e "${GREEN}  ✅ Permessi impostati${NC}"

# Verifica struttura
echo -e "\n${BLUE}Verifica struttura progetto...${NC}"

required_files=(
    "README.md"
    "Makefile"
    ".gitignore"
    ".env.example"
    "docker/Dockerfile"
    "docker/docker-compose.yml"
    "scripts/pdf_processor.py"
    "scripts/process_pdf.sh"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file${NC}"
    else
        echo -e "${RED}  ❌ $file${NC}"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  File mancanti:${NC}"
    for file in "${missing_files[@]}"; do
        echo -e "${YELLOW}    - $file${NC}"
    done
    echo -e "\n${YELLOW}Crea questi file seguendo la documentazione.${NC}"
fi

# Crea file di test se non esiste
echo -e "\n${BLUE}Preparazione ambiente di test...${NC}"

if [ ! -f "tests/sample_files/test.pdf" ]; then
    echo -e "${YELLOW}  ⚠️  File di test non trovato${NC}"
    echo -e "${YELLOW}     Aggiungi un PDF di test in tests/sample_files/test.pdf${NC}"
fi

# Verifica Docker daemon
echo -e "\n${BLUE}Verifica Docker daemon...${NC}"

if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}  ✅ Docker daemon attivo${NC}"
else
    echo -e "${RED}  ❌ Docker daemon non attivo${NC}"
    echo -e "${YELLOW}     Avvia Docker e riprova${NC}"
fi

# Informazioni finali
echo -e "\n${GREEN}🎉 Setup completato!${NC}"
echo -e "\n${BLUE}Prossimi passi:${NC}"
echo -e "1. ${YELLOW}make build${NC}         - Costruisci le immagini Docker"
echo -e "2. ${YELLOW}cp documento.pdf input/${NC} - Aggiungi un PDF di test"
echo -e "3. ${YELLOW}make test-simple${NC}   - Test elaborazione base"
echo -e "4. ${YELLOW}make start-api${NC}     - Avvia API REST"
echo -e "5. ${YELLOW}make test-api${NC}      - Test API completo"

echo -e "\n${BLUE}Documentazione:${NC}"
echo -e "- ${YELLOW}make help${NC}          - Lista comandi disponibili"
echo -e "- ${YELLOW}cat README.md${NC}      - Documentazione completa"

echo -e "\n${GREEN}Buon lavoro! 🚀${NC}"
