import zipfile
import io
import lxml.etree as etree
import pdfplumber
import pikepdf
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def process_xml(self, xml_bytes: bytes) -> Dict[str, Any]:
        """Parses plain Aadhaar XML."""
        try:
            parser = etree.XMLParser(resolve_entities=False, no_network=True)
            root = etree.fromstring(xml_bytes, parser)
            
            # Simple extraction for demo (actual Aadhaar XML has specific tags)
            data = {}
            for elem in root.iter():
                if elem.tag == 'Poi':
                    data['name'] = elem.get('name')
                    data['dob'] = elem.get('dob')
                    data['gender'] = elem.get('gender')
                elif elem.tag == 'Poa':
                    data['state'] = elem.get('state')
                    data['dist'] = elem.get('dist')
                    data['pc'] = elem.get('pc')
            return data
        except Exception as e:
            logger.error(f"XML parsing failed: {e}")
            raise

    def process_zip(self, zip_bytes: bytes, password: str) -> Dict[str, Any]:
        """Processes password-protected Aadhaar ZIP (eAadhaar)."""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                # Find the XML file in the zip
                xml_filename = next((name for name in zf.namelist() if name.endswith('.xml')), None)
                if not xml_filename:
                    raise ValueError("No XML found in ZIP")
                
                with zf.open(xml_filename, pwd=password.encode() if password else None) as f:
                    return self.process_xml(f.read())
        except Exception as e:
            logger.error(f"ZIP processing failed: {e}")
            raise

    def process_pdf(self, pdf_bytes: bytes, password: str) -> Dict[str, Any]:
        """Processes password-protected Aadhaar PDF."""
        try:
            # First attempt to decrypt if password provided
            pdf_stream = io.BytesIO(pdf_bytes)
            if password:
                with pikepdf.open(pdf_stream, password=password) as pdf:
                    decrypted_pdf = io.BytesIO()
                    pdf.save(decrypted_pdf)
                    pdf_stream = decrypted_pdf

            # Extract data using pdfplumber
            data = {}
            with pdfplumber.open(pdf_stream) as pdf:
                # Actual Aadhaar PDF extraction logic is complex (text parsing + QR extraction)
                # Here we do a simplified version
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() or ""
                
                # Mock extraction from text for now
                data['raw_text'] = full_text
            return data
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise
