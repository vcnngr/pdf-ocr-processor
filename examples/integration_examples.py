#!/usr/bin/env python3
"""
Esempi di integrazione PDF OCR Processor con sistemi automatici
"""

import requests
import time
import os
from pathlib import Path

# Configurazione API
API_BASE_URL = "http://localhost:5000"

class PDFOCRClient:
    """Client per l'API PDF OCR Processor"""
    
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Verifica stato dell'API"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, str(e)
    
    def process_sync(self, file_path, output_name=None):
        """Elaborazione sincrona - attende risultato"""
        
        files = {'file': open(file_path, 'rb')}
        data = {}
        
        if output_name:
            data['output_name'] = output_name
        
        try:
            response = self.session.post(
                f"{self.base_url}/process",
                files=files,
                data=data,
                timeout=600
            )
            
            if response.status_code == 200:
                # Salva file risultato
                output_path = output_name or f"{Path(file_path).stem}_ocr.pdf"
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True, output_path
            else:
                return False, response.json().get('error', 'Errore sconosciuto')
                
        except Exception as e:
            return False, str(e)
        finally:
            files['file'].close()
    
    def process_async(self, file_path, output_name=None):
        """Elaborazione asincrona - ritorna job_id"""
        
        files = {'file': open(file_path, 'rb')}
        data = {'async': 'true'}
        
        if output_name:
            data['output_name'] = output_name
        
        try:
            response = self.session.post(
                f"{self.base_url}/process",
                files=files,
                data=data
            )
            
            if response.status_code == 202:
                return True, response.json()['job_id']
            else:
                return False, response.json().get('error', 'Errore sconosciuto')
                
        except Exception as e:
            return False, str(e)
        finally:
            files['file'].close()
    
    def get_job_status(self, job_id):
        """Controlla stato di un job"""
        try:
            response = self.session.get(f"{self.base_url}/status/{job_id}")
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, response.json().get('error', 'Job non trovato')
        except Exception as e:
            return False, str(e)
    
    def download_result(self, job_id, output_path):
        """Scarica risultato di un job completato"""
        try:
            response = self.session.get(f"{self.base_url}/download/{job_id}")
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True, output_path
            else:
                return False, response.json().get('error', 'Download fallito')
        except Exception as e:
            return False, str(e)
    
    def wait_for_completion(self, job_id, timeout=600, check_interval=5):
        """Attende completamento di un job asincrono"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            success, status = self.get_job_status(job_id)
            
            if not success:
                return False, status
            
            if status['status'] == 'completed':
                return True, status
            elif status['status'] == 'error':
                return False, status.get('error', 'Errore sconosciuto')
            
            time.sleep(check_interval)
        
        return False, "Timeout raggiunto"

# ESEMPIO 1: Elaborazione singola sincrona
def example_sync_processing():
    """Esempio di elaborazione sincrona"""
    
    client = PDFOCRClient()
    
    # Verifica che l'API sia online
    healthy, status = client.health_check()
    if not healthy:
        print(f"❌ API non disponibile: {status}")
        return
    
    print("✅ API online")
    
    # Processa un file
    file_path = "documento.pdf"
    if not os.path.exists(file_path):
        print(f"❌ File non trovato: {file_path}")
        return
    
    print(f"🔄 Elaborazione di {file_path}...")
    success, result = client.process_sync(file_path)
    
    if success:
        print(f"✅ Elaborazione completata: {result}")
    else:
        print(f"❌ Errore: {result}")

# ESEMPIO 2: Elaborazione asincrona con monitoraggio
def example_async_processing():
    """Esempio di elaborazione asincrona"""
    
    client = PDFOCRClient()
    
    file_path = "documento_grande.pdf"
    if not os.path.exists(file_path):
        print(f"❌ File non trovato: {file_path}")
        return
    
    # Avvia elaborazione asincrona
    print(f"🚀 Avvio elaborazione asincrona di {file_path}...")
    success, job_id = client.process_async(file_path)
    
    if not success:
        print(f"❌ Errore avvio: {job_id}")
        return
    
    print(f"📋 Job ID: {job_id}")
    
    # Monitora progresso
    print("⏳ Monitoraggio in corso...")
    success, result = client.wait_for_completion(job_id)
    
    if success:
        print(f"✅ Elaborazione completata!")
        print(f"📊 Statistiche: {result}")
        
        # Scarica risultato
        output_path = f"{Path(file_path).stem}_ocr.pdf"
        success, path = client.download_result(job_id, output_path)
        
        if success:
            print(f"📥 File scaricato: {path}")
        else:
            print(f"❌ Errore download: {path}")
    else:
        print(f"❌ Elaborazione fallita: {result}")

# ESEMPIO 3: Elaborazione batch con retry
def example_batch_processing():
    """Esempio di elaborazione batch con gestione errori"""
    
    client = PDFOCRClient()
    input_dir = Path("batch_input")
    output_dir = Path("batch_output")
    
    if not input_dir.exists():
        print(f"❌ Directory non trovata: {input_dir}")
        return
    
    output_dir.mkdir(exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ Nessun file PDF trovato")
        return
    
    print(f"📦 Elaborazione batch: {len(pdf_files)} file")
    
    results = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"🔄 [{i}/{len(pdf_files)}] Elaborando {pdf_file.name}...")
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Avvia job asincrono
                success, job_id = client.process_async(
                    str(pdf_file),
                    f"{pdf_file.stem}_ocr.pdf"
                )
                
                if not success:
                    raise Exception(f"Errore avvio job: {job_id}")
                
                # Attendi completamento
                success, result = client.wait_for_completion(job_id, timeout=300)
                
                if success:
                    # Scarica risultato
                    output_path = output_dir / f"{pdf_file.stem}_ocr.pdf"
                    download_success, download_result = client.download_result(
                        job_id, str(output_path)
                    )
                    
                    if download_success:
                        results.append({
                            'file': pdf_file.name,
                            'status': 'success',
                            'output': output_path.name,
                            'size_mb': output_path.stat().st_size / 1024 / 1024
                        })
                        print(f"  ✅ Completato: {output_path.name}")
                        break
                    else:
                        raise Exception(f"Errore download: {download_result}")
                else:
                    raise Exception(f"Elaborazione fallita: {result}")
                    
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count < max_retries:
                    print(f"  ⚠️  Retry {retry_count}/{max_retries}: {error_msg}")
                    time.sleep(2 ** retry_count)  # Backoff esponenziale
                else:
                    results.append({
                        'file': pdf_file.name,
                        'status': 'error',
                        'error': error_msg
                    })
                    print(f"  ❌ Fallito dopo {max_retries} tentativi: {error_msg}")
    
    # Riepilogo risultati
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'error']
    
    print(f"\n📊 Riepilogo batch:")
    print(f"  ✅ Successi: {len(successful)}")
    print(f"  ❌ Fallimenti: {len(failed)}")
    
    if successful:
        total_size = sum(r['size_mb'] for r in successful)
        print(f"  📁 Dimensione totale output: {total_size:.1f} MB")
    
    if failed:
        print(f"\n❌ File falliti:")
        for result in failed:
            print(f"  - {result['file']}: {result['error']}")

# ESEMPIO 4: Integrazione con sistema di monitoraggio
def example_monitoring_integration():
    """Esempio di integrazione con sistema di monitoraggio"""
    
    import json
    import logging
    from datetime import datetime
    
    # Configurazione logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pdf_processing.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('PDFProcessor')
    
    client = PDFOCRClient()
    
    # Metriche personalizzate
    metrics = {
        'total_processed': 0,
        'total_errors': 0,
        'total_size_mb': 0,
        'avg_processing_time': 0,
        'start_time': datetime.now()
    }
    
    def process_with_metrics(file_path):
        """Processa file con raccolta metriche"""
        
        start_time = time.time()
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        
        logger.info(f"Inizio elaborazione: {file_path} ({file_size_mb:.1f} MB)")
        
        try:
            success, job_id = client.process_async(file_path)
            if not success:
                raise Exception(f"Errore avvio: {job_id}")
            
            success, result = client.wait_for_completion(job_id, timeout=600)
            if not success:
                raise Exception(f"Elaborazione fallita: {result}")
            
            # Scarica risultato
            output_path = f"{Path(file_path).stem}_ocr.pdf"
            success, path = client.download_result(job_id, output_path)
            if not success:
                raise Exception(f"Download fallito: {path}")
            
            # Aggiorna metriche
            processing_time = time.time() - start_time
            output_size_mb = os.path.getsize(output_path) / 1024 / 1024
            
            metrics['total_processed'] += 1
            metrics['total_size_mb'] += output_size_mb
            metrics['avg_processing_time'] = (
                (metrics['avg_processing_time'] * (metrics['total_processed'] - 1) + processing_time) 
                / metrics['total_processed']
            )
            
            logger.info(f"Completato: {output_path} in {processing_time:.1f}s")
            
            return True, {
                'input_file': file_path,
                'output_file': output_path,
                'input_size_mb': file_size_mb,
                'output_size_mb': output_size_mb,
                'processing_time': processing_time,
                'compression_ratio': output_size_mb / file_size_mb if file_size_mb > 0 else 1
            }
            
        except Exception as e:
            metrics['total_errors'] += 1
            logger.error(f"Errore elaborazione {file_path}: {e}")
            return False, str(e)
    
    # Processa alcuni file di esempio
    test_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    results = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            success, result = process_with_metrics(file_path)
            results.append({
                'file': file_path,
                'success': success,
                'result': result
            })
    
    # Report finale
    runtime = (datetime.now() - metrics['start_time']).total_seconds()
    
    report = {
        'summary': {
            'total_files': len(test_files),
            'processed': metrics['total_processed'],
            'errors': metrics['total_errors'],
            'success_rate': metrics['total_processed'] / len(test_files) * 100,
            'total_runtime_seconds': runtime,
            'avg_processing_time': metrics['avg_processing_time'],
            'total_output_size_mb': metrics['total_size_mb']
        },
        'details': results
    }
    
    # Salva report
    with open('processing_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Report salvato: processing_report.json")
    logger.info(f"Tasso successo: {report['summary']['success_rate']:.1f}%")

# ESEMPIO 5: Integrazione con webhook
def example_webhook_integration():
    """Esempio di integrazione con sistema webhook"""
    
    from threading import Thread
    import queue
    
    # Coda per gestire notifiche
    notification_queue = queue.Queue()
    
    def webhook_sender():
        """Thread che invia notifiche webhook"""
        webhook_url = "https://your-system.com/webhook/pdf-processed"
        
        while True:
            try:
                notification = notification_queue.get(timeout=60)
                
                # Invia notifica
                response = requests.post(
                    webhook_url,
                    json=notification,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"✅ Webhook inviato: {notification['job_id']}")
                else:
                    print(f"❌ Webhook fallito: {response.status_code}")
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Errore webhook: {e}")
    
    # Avvia thread webhook
    webhook_thread = Thread(target=webhook_sender, daemon=True)
    webhook_thread.start()
    
    client = PDFOCRClient()
    
    # Processa file con notifiche webhook
    file_path = "documento.pdf"
    if os.path.exists(file_path):
        success, job_id = client.process_async(file_path)
        
        if success:
            # Monitora e invia notifiche
            while True:
                success, status = client.get_job_status(job_id)
                
                if success:
                    notification = {
                        'job_id': job_id,
                        'file': file_path,
                        'status': status['status'],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if status['status'] == 'completed':
                        notification['output_size'] = status.get('output_size', 0)
                        notification_queue.put(notification)
                        break
                    elif status['status'] == 'error':
                        notification['error'] = status.get('error', 'Errore sconosciuto')
                        notification_queue.put(notification)
                        break
                
                time.sleep(10)

if __name__ == "__main__":
    print("=== Esempi di Integrazione PDF OCR Processor ===\n")
    
    print("1. Elaborazione sincrona")
    example_sync_processing()
    
    print("\n2. Elaborazione asincrona")
    example_async_processing()
    
    print("\n3. Elaborazione batch")
    example_batch_processing()
    
    print("\n4. Con monitoraggio metriche")
    example_monitoring_integration()
    
    print("\n5. Con webhook")
    example_webhook_integration()
