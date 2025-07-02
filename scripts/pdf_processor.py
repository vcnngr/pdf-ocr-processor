#!/usr/bin/env python3
"""
PDF Content Analyzer and OCR Processor
Analizza il contenuto di un PDF e applica OCR se necessario
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance
import tempfile
import shutil

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, input_path, output_path, temp_dir="/app/temp"):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
    def analyze_pdf_content(self):
        """Analizza il contenuto del PDF per determinare se ha testo estraibile"""
        try:
            # Prova ad estrarre testo con PyPDF2
            with open(self.input_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_text = ""
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    total_text += text
                
                # Conta caratteri significativi (no spazi/newline)
                significant_chars = len([c for c in total_text if c.isalnum()])
                
                logger.info(f"Caratteri significativi estratti: {significant_chars}")
                
                # Se ha meno di 100 caratteri significativi, considera come immagine
                if significant_chars < 100:
                    return "needs_ocr"
                else:
                    # Verifica qualità del testo estratto
                    if self._is_text_quality_good(total_text):
                        return "has_text"
                    else:
                        return "needs_ocr"
                        
        except Exception as e:
            logger.warning(f"Errore nell'analisi con PyPDF2: {e}")
            return "needs_ocr"
    
    def _is_text_quality_good(self, text):
        """Verifica se il testo estratto è di buona qualità"""
        # Controlla rapporto caratteri validi vs totali
        if len(text) == 0:
            return False
            
        valid_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in '.,;:!?-')
        ratio = valid_chars / len(text)
        
        # Se meno del 80% sono caratteri validi, probabilmente è testo corrotto
        return ratio > 0.8
    
    def optimize_image_for_ocr(self, image):
        """Ottimizza l'immagine per migliorare la precisione OCR"""
        # Converti in scala di grigi
        if image.mode != 'L':
            image = image.convert('L')
        
        # Migliora il contrasto
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Migliora la nitidezza
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        # Ridimensiona se troppo piccola (migliora OCR)
        width, height = image.size
        if width < 1000 or height < 1000:
            scale_factor = max(1000/width, 1000/height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def perform_ocr(self):
        """Esegue OCR sul PDF"""
        logger.info("Inizio processo OCR...")
        
        # Converti PDF in immagini
        try:
            pages = convert_from_path(
                self.input_path,
                dpi=300,
                output_folder=self.temp_dir,
                fmt='png'
            )
            logger.info(f"Convertite {len(pages)} pagine in immagini")
        except Exception as e:
            logger.error(f"Errore nella conversione PDF->immagini: {e}")
            return False
        
        # Processa ogni pagina con OCR
        ocr_results = []
        for i, page in enumerate(pages):
            try:
                logger.info(f"Processing pagina {i+1}/{len(pages)}")
                
                # Ottimizza immagine
                optimized_page = self.optimize_image_for_ocr(page)
                
                # Configura Tesseract per italiano e inglese
                custom_config = r'--oem 3 --psm 1 -c preserve_interword_spaces=1'
                
                # Esegui OCR
                text = pytesseract.image_to_string(
                    optimized_page,
                    lang='ita+eng',
                    config=custom_config
                )
                
                ocr_results.append(text)
                logger.info(f"OCR completato per pagina {i+1}, caratteri: {len(text)}")
                
            except Exception as e:
                logger.error(f"Errore OCR pagina {i+1}: {e}")
                ocr_results.append("")
        
        # Crea PDF ricercabile usando tesseract direttamente
        return self._create_searchable_pdf(pages, ocr_results)
    
    def _create_searchable_pdf(self, pages, ocr_results):
        """Crea PDF ricercabile usando tesseract"""
        try:
            # Salva temporaneamente le immagini ottimizzate
            temp_images = []
            for i, page in enumerate(pages):
                optimized_page = self.optimize_image_for_ocr(page)
                temp_path = self.temp_dir / f"page_{i:03d}.png"
                optimized_page.save(temp_path, 'PNG', dpi=(300, 300))
                temp_images.append(temp_path)
            
            # Usa tesseract per creare PDF ricercabile
            pdf_files = []
            for i, img_path in enumerate(temp_images):
                output_pdf = self.temp_dir / f"page_{i:03d}.pdf"
                
                cmd = [
                    'tesseract',
                    str(img_path),
                    str(output_pdf.with_suffix('')),
                    '-l', 'ita+eng',
                    '--oem', '3',
                    '--psm', '1',
                    'pdf'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    pdf_files.append(output_pdf)
                    logger.info(f"PDF creato per pagina {i+1}")
                else:
                    logger.error(f"Errore tesseract pagina {i+1}: {result.stderr}")
            
            # Unisci tutti i PDF
            if pdf_files:
                return self._merge_pdfs(pdf_files)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Errore nella creazione PDF ricercabile: {e}")
            return False
    
    def _merge_pdfs(self, pdf_files):
        """Unisce più PDF in uno solo"""
        try:
            cmd = ['qpdf', '--empty', '--pages'] + [str(f) for f in pdf_files] + ['--', str(self.output_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"PDF finale creato: {self.output_path}")
                return True
            else:
                logger.error(f"Errore merge PDF: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Errore nell'unione PDF: {e}")
            return False
    
    def optimize_existing_pdf(self):
        """Ottimizza un PDF che ha già testo ricercabile"""
        try:
            cmd = [
                'qpdf',
                '--linearize',
                '--optimize-images',
                '--compress-streams=y',
                str(self.input_path),
                str(self.output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("PDF ottimizzato con successo")
                return True
            else:
                logger.error(f"Errore ottimizzazione: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Errore nell'ottimizzazione: {e}")
            return False
    
    def process(self):
        """Processo principale"""
        try:
            logger.info(f"Inizio elaborazione: {self.input_path}")
            
            # Analizza contenuto
            content_type = self.analyze_pdf_content()
            logger.info(f"Tipo di contenuto rilevato: {content_type}")
            
            if content_type == "needs_ocr":
                success = self.perform_ocr()
            else:
                success = self.optimize_existing_pdf()
            
            if success:
                # Statistiche finali
                input_size = self.input_path.stat().st_size
                output_size = self.output_path.stat().st_size
                
                logger.info(f"Elaborazione completata!")
                logger.info(f"Dimensione originale: {input_size / 1024:.1f} KB")
                logger.info(f"Dimensione finale: {output_size / 1024:.1f} KB")
                logger.info(f"Rapporto compressione: {output_size/input_size:.2f}")
                
                return True
            else:
                logger.error("Elaborazione fallita")
                return False
                
        except Exception as e:
            logger.error(f"Errore generale: {e}")
            return False
        
        finally:
            # Pulizia file temporanei
            try:
                shutil.rmtree(self.temp_dir)
                logger.info("File temporanei eliminati")
            except:
                pass

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 pdf_processor.py <input.pdf> <output.pdf>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"File di input non trovato: {input_file}")
        sys.exit(1)
    
    processor = PDFProcessor(input_file, output_file)
    success = processor.process()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
