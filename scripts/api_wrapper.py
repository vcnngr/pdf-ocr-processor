#!/usr/bin/env python3
"""
API REST wrapper per PDF OCR Processor
Permette integrazione con sistemi automatici via HTTP
"""

from flask import Flask, request, jsonify, send_file
import os
import tempfile
import shutil
import subprocess
import logging
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import threading
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory di lavoro
WORK_DIR = "/tmp/pdf_processor"
os.makedirs(WORK_DIR, exist_ok=True)

# Storage per job in corso
active_jobs = {}

class JobStatus:
    QUEUED = "queued"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    ERROR = "error"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def process_pdf_async(job_id, input_path, output_path):
    """Processa PDF in background"""
    try:
        active_jobs[job_id]['status'] = JobStatus.PROCESSING
        active_jobs[job_id]['started_at'] = datetime.now()
        
        # Esegui il processore Docker
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{os.path.dirname(input_path)}:/app/input',
            '-v', f'{os.path.dirname(output_path)}:/app/output',
            'pdf-ocr-processor',
            os.path.basename(input_path),
            os.path.basename(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0 and os.path.exists(output_path):
            active_jobs[job_id]['status'] = JobStatus.COMPLETED
            active_jobs[job_id]['completed_at'] = datetime.now()
            active_jobs[job_id]['output_size'] = os.path.getsize(output_path)
        else:
            active_jobs[job_id]['status'] = JobStatus.ERROR
            active_jobs[job_id]['error'] = result.stderr
            
    except subprocess.TimeoutExpired:
        active_jobs[job_id]['status'] = JobStatus.ERROR
        active_jobs[job_id]['error'] = "Timeout: elaborazione troppo lunga"
    except Exception as e:
        active_jobs[job_id]['status'] = JobStatus.ERROR  
        active_jobs[job_id]['error'] = str(e)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check per monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_jobs': len([j for j in active_jobs.values() if j['status'] == JobStatus.PROCESSING])
    })

@app.route('/process', methods=['POST'])
def process_pdf():
    """Endpoint principale per processing PDF"""
    
    # Verifica presenza file
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file fornito'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nessun file selezionato'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Solo file PDF sono supportati'}), 400
    
    # Parametri opzionali
    async_mode = request.form.get('async', 'false').lower() == 'true'
    output_name = request.form.get('output_name', '')
    
    try:
        # Crea job ID univoco
        job_id = str(uuid.uuid4())
        job_dir = os.path.join(WORK_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Salva file input
        filename = secure_filename(file.filename)
        input_path = os.path.join(job_dir, filename)
        file.save(input_path)
        
        # Determina nome output
        if not output_name:
            base_name = os.path.splitext(filename)[0]
            output_name = f"{base_name}_ocr.pdf"
        
        output_path = os.path.join(job_dir, output_name)
        
        # Inizializza job tracking
        active_jobs[job_id] = {
            'id': job_id,
            'status': JobStatus.QUEUED,
            'input_file': filename,
            'output_file': output_name,
            'input_size': os.path.getsize(input_path),
            'created_at': datetime.now(),
            'input_path': input_path,
            'output_path': output_path
        }
        
        if async_mode:
            # Processing asincrono
            thread = threading.Thread(
                target=process_pdf_async,
                args=(job_id, input_path, output_path)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'job_id': job_id,
                'status': JobStatus.QUEUED,
                'message': 'Job avviato, usa /status/{job_id} per monitorare'
            }), 202
            
        else:
            # Processing sincrono
            process_pdf_async(job_id, input_path, output_path)
            
            if active_jobs[job_id]['status'] == JobStatus.COMPLETED:
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=output_name,
                    mimetype='application/pdf'
                )
            else:
                return jsonify({
                    'error': active_jobs[job_id].get('error', 'Errore sconosciuto')
                }), 500
                
    except Exception as e:
        logger.error(f"Errore processing: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Controlla stato di un job"""
    
    if job_id not in active_jobs:
        return jsonify({'error': 'Job non trovato'}), 404
    
    job = active_jobs[job_id].copy()
    
    # Rimuovi percorsi interni dalla risposta
    job.pop('input_path', None)
    job.pop('output_path', None)
    
    # Calcola durata se in corso
    if job['status'] == JobStatus.PROCESSING and 'started_at' in job:
        duration = (datetime.now() - job['started_at']).total_seconds()
        job['duration_seconds'] = round(duration, 1)
    
    return jsonify(job)

@app.route('/download/<job_id>', methods=['GET'])
def download_result(job_id):
    """Scarica risultato di un job completato"""
    
    if job_id not in active_jobs:
        return jsonify({'error': 'Job non trovato'}), 404
    
    job = active_jobs[job_id]
    
    if job['status'] != JobStatus.COMPLETED:
        return jsonify({'error': f'Job non completato (status: {job["status"]})'}), 400
    
    if not os.path.exists(job['output_path']):
        return jsonify({'error': 'File di output non trovato'}), 404
    
    return send_file(
        job['output_path'],
        as_attachment=True,
        download_name=job['output_file'],
        mimetype='application/pdf'
    )

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """Lista tutti i job (per debugging)"""
    
    jobs = []
    for job in active_jobs.values():
        job_info = job.copy()
        job_info.pop('input_path', None)
        job_info.pop('output_path', None)
        jobs.append(job_info)
    
    return jsonify({
        'jobs': jobs,
        'total': len(jobs)
    })

@app.route('/cleanup', methods=['POST'])
def cleanup_jobs():
    """Pulisce job completati (manuale)"""
    
    cleaned = 0
    for job_id in list(active_jobs.keys()):
        job = active_jobs[job_id]
        
        # Rimuovi job completati da più di 1 ora
        if job['status'] in [JobStatus.COMPLETED, JobStatus.ERROR]:
            completed_at = job.get('completed_at', job.get('created_at'))
            if (datetime.now() - completed_at).total_seconds() > 3600:
                # Rimuovi file
                job_dir = os.path.dirname(job.get('input_path', ''))
                if os.path.exists(job_dir):
                    shutil.rmtree(job_dir)
                
                # Rimuovi da memoria
                del active_jobs[job_id]
                cleaned += 1
    
    return jsonify({
        'message': f'Ripuliti {cleaned} job',
        'remaining': len(active_jobs)
    })

# Auto-cleanup ogni ora
def auto_cleanup():
    """Cleanup automatico in background"""
    while True:
        time.sleep(3600)  # 1 ora
        try:
            with app.app_context():
                cleanup_jobs()
        except:
            pass

# Avvia thread di cleanup
cleanup_thread = threading.Thread(target=auto_cleanup)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
