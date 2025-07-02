# Makefile per PDF OCR Processor
# Semplifica gestione e deployment

.PHONY: help build start stop clean logs test deploy

# Configurazione
PROJECT_NAME = pdf-ocr-processor
API_PORT = 5000
VERSION = latest

# Colori per output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Mostra questo aiuto
	@echo "$(BLUE)PDF OCR Processor - Comandi Disponibili$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Inizializza ambiente di sviluppo
	@echo "$(BLUE)Inizializzazione ambiente...$(NC)"
	mkdir -p input output temp batch_input batch_output api_temp
	@echo "$(GREEN)✓ Directory create$(NC)"

build: ## Costruisce le immagini Docker
	@echo "$(BLUE)Costruzione immagini Docker...$(NC)"
	@docker build -t $(PROJECT_NAME):$(VERSION) .
	@docker build -f Dockerfile.api -t $(PROJECT_NAME)-api:$(VERSION) .
	@echo "$(GREEN)✓ Immagini costruite$(NC)"

start-processor: setup ## Avvia solo il processore base
	@echo "$(BLUE)Avvio processore base...$(NC)"
	@docker-compose --profile manual up --build

start-api: build ## Avvia API REST
	@echo "$(BLUE)Avvio API REST su porta $(API_PORT)...$(NC)"
	@docker-compose --profile api up -d
	@echo "$(GREEN)✓ API avviata su http://localhost:$(API_PORT)$(NC)"
	@echo "Test: curl http://localhost:$(API_PORT)/health"

start-all: build ## Avvia tutto (API + Monitor)
	@echo "$(BLUE)Avvio stack completo...$(NC)"
	@docker-compose --profile api --profile monitor up -d
	@echo "$(GREEN)✓ Stack completo avviato$(NC)"

stop: ## Ferma tutti i servizi
	@echo "$(BLUE)Arresto servizi...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Servizi fermati$(NC)"

clean: ## Pulisce tutto (container, immagini, volumi)
	@echo "$(YELLOW)Pulizia completa...$(NC)"
	@docker-compose down -v --remove-orphans
	@docker system prune -f
	@rm -rf temp/* api_temp/* output/*
	@echo "$(GREEN)✓ Pulizia completata$(NC)"

logs: ## Mostra log dei servizi
	@docker-compose logs -f

logs-api: ## Mostra solo log API
	@docker-compose logs -f pdf-api

status: ## Mostra stato dei servizi
	@echo "$(BLUE)Stato servizi:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(BLUE)Immagini:$(NC)"
	@docker images | grep $(PROJECT_NAME)

# Test e validazione
test-health: ## Test health check API
	@echo "$(BLUE)Test health check...$(NC)"
	@curl -f http://localhost:$(API_PORT)/health || (echo "$(RED)✗ API non risponde$(NC)" && exit 1)
	@echo "$(GREEN)✓ API online$(NC)"

test-simple: ## Test elaborazione semplice
	@echo "$(BLUE)Test elaborazione semplice...$(NC)"
	@if [ ! -f input/test.pdf ]; then \
		echo "$(RED)✗ File input/test.pdf non trovato$(NC)"; \
		echo "Crea un file PDF di test in input/test.pdf"; \
		exit 1; \
	fi
	@docker run --rm \
		-v $(PWD)/input:/app/input \
		-v $(PWD)/output:/app/output \
		$(PROJECT_NAME):$(VERSION) test.pdf
	@echo "$(GREEN)✓ Test completato$(NC)"

test-api: ## Test API completo
	@echo "$(BLUE)Test API completo...$(NC)"
	@if [ ! -f input/test.pdf ]; then \
		echo "$(RED)✗ File input/test.pdf non trovato$(NC)"; \
		exit 1; \
	fi
	@python3 -c "
import requests
import time

# Test sincrono
print('Test sincrono...')
with open('input/test.pdf', 'rb') as f:
    response = requests.post('http://localhost:$(API_PORT)/process', files={'file': f})
    
if response.status_code == 200:
    with open('output/test_api_sync.pdf', 'wb') as f:
        f.write(response.content)
    print('✓ Test sincrono OK')
else:
    print(f'✗ Test sincrono fallito: {response.status_code}')

# Test asincrono
print('Test asincrono...')
with open('input/test.pdf', 'rb') as f:
    response = requests.post('http://localhost:$(API_PORT)/process', 
                           files={'file': f}, 
                           data={'async': 'true'})

if response.status_code == 202:
    job_id = response.json()['job_id']
    print(f'Job ID: {job_id}')
    
    # Attendi completamento
    for i in range(30):
        status = requests.get(f'http://localhost:$(API_PORT)/status/{job_id}').json()
        if status['status'] == 'completed':
            # Scarica risultato
            result = requests.get(f'http://localhost:$(API_PORT)/download/{job_id}')
            with open('output/test_api_async.pdf', 'wb') as f:
                f.write(result.content)
            print('✓ Test asincrono OK')
            break
        elif status['status'] == 'error':
            print(f'✗ Test asincrono fallito: {status.get(\"error\")}')
            break
        time.sleep(2)
    else:
        print('✗ Test asincrono timeout')
else:
    print(f'✗ Test asincrono fallito: {response.status_code}')
"
	@echo "$(GREEN)✓ Test API completato$(NC)"

batch: ## Elaborazione batch
	@echo "$(BLUE)Avvio elaborazione batch...$(NC)"
	@if [ -z "$$(ls batch_input/*.pdf 2>/dev/null)" ]; then \
		echo "$(RED)✗ Nessun file PDF in batch_input/$(NC)"; \
		exit 1; \
	fi
	@docker-compose --profile batch run --rm pdf-batch-processor
	@echo "$(GREEN)✓ Elaborazione batch completata$(NC)"

monitor: ## Avvia monitoraggio
	@echo "$(BLUE)Avvio monitoraggio...$(NC)"
	@docker-compose --profile monitor up pdf-monitor

# Deployment e produzione
deploy-production: ## Deploy in produzione
	@echo "$(BLUE)Deploy produzione...$(NC)"
	@echo "$(YELLOW)⚠️  Configurare prima:$(NC)"
	@echo "- Variabili ambiente in .env.production"
	@echo "- Certificati SSL per HTTPS"
	@echo "- Backup automatico"
	@echo "- Monitoraggio esterno"
	@read -p "Continuare? (y/N) " confirm && [ "$$confirm" = "y" ]
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✓ Deploy completato$(NC)"

backup: ## Backup configurazione
	@echo "$(BLUE)Backup configurazione...$(NC)"
	@mkdir -p backups
	@tar -czf backups/config-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		docker-compose.yml Dockerfile* *.py *.sh Makefile
	@echo "$(GREEN)✓ Backup salvato in backups/$(NC)"

# Utilità sviluppo
shell-processor: ## Shell nel container processore
	@docker run --rm -it \
		-v $(PWD)/input:/app/input \
		-v $(PWD)/output:/app/output \
		$(PROJECT_NAME):$(VERSION) bash

shell-api: ## Shell nel container API
	@docker-compose exec pdf-api bash

update: ## Aggiorna dipendenze
	@echo "$(BLUE)Aggiornamento dipendenze...$(NC)"
	@docker-compose pull
	@docker system prune -f
	@echo "$(GREEN)✓ Aggiornamento completato$(NC)"

# Metriche e performance
metrics: ## Mostra metriche di utilizzo
	@echo "$(BLUE)Metriche di utilizzo:$(NC)"
	@echo ""
	@echo "$(BLUE)File processati:$(NC)"
	@find output -name "*.pdf" | wc -l | xargs echo "  Output files:"
	@du -sh output 2>/dev/null | cut -f1 | xargs echo "  Output size:"
	@echo ""
	@echo "$(BLUE)Container stats:$(NC)"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep pdf || echo "  Nessun container attivo"

performance-test: ## Test performance con file multipli
	@echo "$(BLUE)Test performance...$(NC)"
	@mkdir -p perf_test_input perf_test_output
	@echo "Crea file di test in perf_test_input/"
	@echo "Esegui: make batch INPUT_DIR=perf_test_input OUTPUT_DIR=perf_test_output"

# Debugging
debug: ## Modalità debug
	@echo "$(BLUE)Modalità debug attiva$(NC)"
	@docker-compose -f docker-compose.yml -f docker-compose.debug.yml up

debug-logs: ## Log dettagliati per debugging
	@docker-compose logs --tail=100 -f

# Info sistema
info: ## Informazioni sistema
	@echo "$(BLUE)Informazioni Sistema:$(NC)"
	@echo "Docker version: $$(docker --version)"
	@echo "Docker compose version: $$(docker-compose --version)"
	@echo "Spazio disco: $$(df -h . | tail -1 | awk '{print $$4}') disponibile"
	@echo "Memoria: $$(free -h | awk '/^Mem:/ {print $$7}') disponibile"
	@echo ""
	@echo "$(BLUE)Configurazione Progetto:$(NC)"
	@echo "Nome progetto: $(PROJECT_NAME)"
	@echo "Porta API: $(API_PORT)"
	@echo "Versione: $(VERSION)"
