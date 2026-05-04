"""
Document processor for Aadhaar PDF and XML ZIP.
Merged: user's pikepdf/pdfplumber + mine's PyMuPDF QR page scan + pyzipper AES-256.
"""
import io
import zipfile
import logging
import lxml.etree as etree
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DocumentProcessor:

    # ── XML ──────────────────────────────────────────────────────────────
    def process_xml(self, xml_bytes: bytes) -> Dict[str, Any]:
        """Parse Aadhaar XML with entity injection protection."""
        try:
            parser = etree.XMLParser(resolve_entities=False, no_network=True)
            root = etree.fromstring(xml_bytes, parser)
            data: Dict[str, Any] = {}
            poi = root.find("Poi")
            poa = root.find("Poa")
            photo_elem = root.find(".//Pht")

            if poi is not None:
                data["name"]        = poi.get("name") or poi.get("n")
                data["dob"]         = poi.get("dob")
                data["gender"]      = poi.get("gender") or poi.get("g")
                data["email_hash"]  = poi.get("e")
                data["mobile_hash"] = poi.get("m")

            uid = root.get("uid") or root.get("referenceId", "")
            data["uid"]         = uid
            data["masked_uid"]  = f"XXXX XXXX {uid[-4:]}" if len(uid) >= 4 else "XXXX XXXX XXXX"

            if poa is not None:
                data["address"] = {
                    "house":    poa.get("house") or poa.get("co"),
                    "street":   poa.get("street"),
                    "landmark": poa.get("lm"),
                    "city":     poa.get("loc") or poa.get("vtc"),
                    "district": poa.get("dist"),
                    "state":    poa.get("state"),
                    "pincode":  poa.get("pc"),
                }

            if photo_elem is not None and photo_elem.text:
                import base64
                try:
                    data["photo"] = base64.b64decode(photo_elem.text)
                except Exception:
                    data["photo"] = None

            return data
        except Exception as e:
            logger.error(f"XML parsing failed: {e}")
            raise

    # ── ZIP (eAadhaar) ───────────────────────────────────────────────────
    def process_zip(self, zip_bytes: bytes, password: str) -> Dict[str, Any]:
        """AES-256 ZIP via pyzipper, falls back to standard zipfile."""
        try:
            import pyzipper
            with pyzipper.AESZipFile(io.BytesIO(zip_bytes)) as zf:
                zf.setpassword(password.encode())
                xml_name = next((n for n in zf.namelist() if n.lower().endswith(".xml")), None)
                if not xml_name:
                    raise ValueError("No XML file found in ZIP")
                return self.process_xml(zf.read(xml_name))
        except Exception:
            pass

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                zf.setpassword(password.encode())
                xml_name = next((n for n in zf.namelist() if n.lower().endswith(".xml")), None)
                if not xml_name:
                    raise ValueError("No XML file found in ZIP")
                return self.process_xml(zf.read(xml_name))
        except RuntimeError:
            raise ValueError("Incorrect ZIP password")
        except Exception as e:
            logger.error(f"ZIP processing failed: {e}")
            raise

    # ── PDF ──────────────────────────────────────────────────────────────
    def process_pdf(self, pdf_bytes: bytes, password: str) -> Dict[str, Any]:
        """
        1. Decrypt with pikepdf
        2. Scan each page for QR via PyMuPDF + decoder cascade
        3. Fall back to embedded XML attachment
        """
        decrypted = self._decrypt_pdf(pdf_bytes, password)

        result = self._extract_qr_from_pdf(decrypted)
        if result:
            return result

        result = self._extract_embedded_xml(decrypted)
        if result:
            return result

        raise ValueError("No Aadhaar QR or XML found in PDF")

    def _decrypt_pdf(self, pdf_bytes: bytes, password: str) -> bytes:
        try:
            import pikepdf
            with pikepdf.open(io.BytesIO(pdf_bytes), password=password) as pdf:
                out = io.BytesIO()
                pdf.save(out)
                return out.getvalue()
        except Exception:
            return pdf_bytes

    def _extract_qr_from_pdf(self, pdf_bytes: bytes) -> Optional[Dict[str, Any]]:
        try:
            import fitz
            import numpy as np
            from src.engines.qr_decoder import decode_qr
            from src.engines.aadhaar_verifier import verify_aadhaar_qr

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page_num in range(min(doc.page_count, 3)):
                pix = doc[page_num].get_pixmap(matrix=fitz.Matrix(3.0, 3.0), colorspace=fitz.csGRAY)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
                qr_data = decode_qr(img)
                if qr_data:
                    doc.close()
                    return verify_aadhaar_qr(qr_data)
            doc.close()
        except Exception as e:
            logger.warning(f"PDF QR scan failed: {e}")
        return None

    def _extract_embedded_xml(self, pdf_bytes: bytes) -> Optional[Dict[str, Any]]:
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for name in doc.embfile_names():
                if name.lower().endswith(".xml"):
                    xml_bytes = doc.embfile_get(name)
                    doc.close()
                    return self.process_xml(xml_bytes)
            doc.close()
        except Exception as e:
            logger.warning(f"PDF XML extraction failed: {e}")
        return None
