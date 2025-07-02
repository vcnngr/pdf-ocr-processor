# 🔍 PDF OCR Processor

> **Trasforma qualsiasi PDF in un documento ricercabile e ottimizzato per sistemi automatici**

## ⚡ Quick Start

```bash
git clone <repository>
cd pdf-ocr-processor
make setup build
cp your-document.pdf input/
make start-api
```

**Boom!** Il tuo PDF è ora ricercabile e ottimizzato.

## 🎯 Cosa Fa

- **🤖 Analisi Intelligente**: Rileva automaticamente se serve OCR o solo ottimizzazione
- **📄 OCR Avanzato**: Tesseract ottimizzato per italiano/inglese con preprocessing
- **⚡ Container Distruttibili**: Ogni elaborazione è isolata e si pulisce da sola
- **🔌 API REST**: Integrazione immediata con qualsiasi sistema
- **📦 Batch Processing**: Elabora centinaia di file automaticamente
- **📊 Monitoraggio**: Tracciamento completo delle operazioni

## 🚀 Utilizzo

### Singolo File
```bash
# Elaborazione semplice
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output pdf-ocr-processor documento.pdf

# Via API
curl -X POST -F "file=@documento.pdf" http://localhost:5000/process > output.pdf
```

### Batch Processing
```bash
cp *.pdf batch_input/
make batch
```

### Monitoraggio
```bash
make monitor    # Real-time monitoring
make metrics    # Usage statistics
```

## 🛠️ Requisiti

- Docker & Docker Compose
- 2GB RAM minimo
- Spazio disco per file temporanei

## 📋 Comandi Principali

```bash
make build          # Costruisce immagini Docker
make start-api      # Avvia API REST
make test-api       # Test funzionalità
make batch          # Elaborazione batch
make monitor        # Monitoraggio real-time
make clean          # Pulizia completa
```

## 🔧 Caratteristiche Tecniche

**Input**: PDF scansionati, nativi, corrotti  
**Output**: PDF ricercabili, ottimizzati, compressi  
**Lingue**: Italiano, Inglese (espandibile)  
**Formati**: Mantiene layout originale  
**Performance**: ~30s per pagina A4 a 300 DPI  

## 🎛️ Modalità Operative

| Modalità | Uso | Comando |
|----------|-----|---------|
| **Sync** | File singoli | `curl -X POST -F "file=@doc.pdf" /process` |
| **Async** | File grandi | `curl -X POST -F "file=@doc.pdf" -F "async=true" /process` |
| **Batch** | Volumi elevati | `make batch` |
| **Monitor** | Produzione | `make start-all` |

## 🔗 Integrazione Sistemi

**Webhook Support**: Notifiche automatiche  
**REST API**: Integrazione universale  
**Health Checks**: Monitoring esterno  
**Metrics**: Prometheus-ready  

## 🏗️ Architettura

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   API REST  │────│  OCR Engine  │────│  PDF Output │
│   (Flask)   │    │ (Tesseract)  │    │ (Optimized) │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │                   │
   ┌───────┐         ┌──────────┐        ┌──────────┐
   │ Queue │         │ PreProc  │        │ PostProc │
   │ Mgmt  │         │ Images   │        │ Compress │
   └───────┘         └──────────┘        └──────────┘
```

## 🔒 Sicurezza

- Container isolati senza privilegi elevati
- Pulizia automatica file temporanei  
- Limiti risorse configurabili
- Nessuna persistenza dati sensibili

## 📈 Scalabilità

**Orizzontale**: Multiple istanze API  
**Verticale**: Resource limits configurabili  
**Load Balancing**: Nginx incluso  
**Auto-scaling**: Kubernetes-ready  

## 🎯 Casi d'Uso

✅ **Digitalizzazione archivi**: Trasforma scansioni in documenti ricercabili  
✅ **Pipeline automatiche**: Integra in workflow esistenti  
✅ **Compliance**: Rende accessibili documenti legacy  
✅ **Search systems**: Abilita ricerca full-text  
✅ **Data extraction**: Prepara per NLP/AI  

## 🆘 Troubleshooting

```bash
make logs           # Verifica log errori
make test-health    # Test stato servizi  
make clean setup    # Reset completo
```

**Errori comuni:**  
- `File non trovato` → Verifica mount volumes
- `Memory limit` → Aumenta limiti Docker  
- `OCR fallito` → Controlla qualità immagini

## 🤝 Contributi

Fork → Branch → Commit → Pull Request

**Aree di sviluppo:**  
- Nuove lingue OCR
- Algoritmi preprocessing  
- Ottimizzazioni performance
- Integrazione cloud providers

---

**🎉 Trasforma i tuoi PDF in documenti intelligenti in pochi minuti!**

*Made with ❤️ for automation systems*
