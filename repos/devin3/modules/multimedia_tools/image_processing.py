# Devin/modules/multimedia_tools/image_processing.py
# Purpose: A comprehensive toolkit for image processing, including EXIF data
#          analysis, OCR, and steganography.

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

try:
    from stegano import lsb
    STEGANO_AVAILABLE = True
except ImportError:
    STEGANO_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("ImageProcessor")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class ImageProcessor:
    """
    Provides a suite of tools for image analysis and manipulation.
    """
    def __init__(self, image_path: Optional[Path] = None):
        self.image_path = image_path
        self.image: Optional[Image.Image] = None
        if self.image_path and self.image_path.is_file():
            self._load_image()

    def _load_image(self):
        """Loads the image from the specified path."""
        if not PILLOW_AVAILABLE: raise ImportError("Pillow is required.")
        try:
            self.image = Image.open(self.image_path)
            logger.info(f"Image loaded from {self.image_path}")
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            self.image = None

    def extract_exif_data(self) -> Optional[Dict[str, Any]]:
        """Extracts and decodes EXIF metadata from the image."""
        if not self.image or not PIEXIF_AVAILABLE: return None
        logger.info("Extracting EXIF data...")
        try:
            exif_dict = piexif.load(self.image.info.get('exif', b''))
            decoded_exif = {}
            for ifd_name in exif_dict:
                if ifd_name == "thumbnail": continue
                for tag, value in exif_dict[ifd_name].items():
                    tag_name = piexif.TAGS[ifd_name][tag]["name"]
                    # Decode byte values
                    if isinstance(value, bytes):
                        try:
                            decoded_exif[tag_name] = value.decode(errors='ignore').strip('\x00')
                        except:
                            decoded_exif[tag_name] = repr(value)
                    else:
                        decoded_exif[tag_name] = value
            return decoded_exif
        except Exception as e:
            logger.warning(f"Could not read EXIF data: {e}")
            return None

    def extract_text_with_ocr(self) -> Optional[str]:
        """Performs OCR on the image to extract text."""
        if not self.image or not PYTESSERACT_AVAILABLE: return None
        logger.info("Performing OCR to extract text...")
        try:
            # A check to see if Tesseract executable is available
            pytesseract.get_tesseract_version()
            text = pytesseract.image_to_string(self.image)
            logger.info(f"OCR complete. Found {len(text)} characters.")
            return text
        except Exception as e:
            logger.error(f"OCR failed. Is the Tesseract engine installed and in your PATH? Error: {e}")
            return None

    def hide_data_steganography(self, data_to_hide: str, output_path: Path):
        """Hides a string within the image using LSB steganography."""
        if not self.image_path or not STEGANO_AVAILABLE: return False
        logger.info(f"Hiding data in {self.image_path}...")
        try:
            secret_image = lsb.hide(str(self.image_path), data_to_hide)
            secret_image.save(output_path)
            logger.warning(f"Data hidden successfully. New image saved to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Steganography hiding failed: {e}")
            return False

    def reveal_data_steganography(self) -> Optional[str]:
        """Reveals a secret message hidden in the image."""
        if not self.image_path or not STEGANO_AVAILABLE: return None
        logger.info(f"Attempting to reveal hidden data from {self.image_path}...")
        try:
            message = lsb.reveal(str(self.image_path))
            return message
        except IndexError:
            logger.info("No hidden data found in the image.")
            return None
        except Exception as e:
            logger.error(f"Steganography reveal failed: {e}")
            return None
        
# --- Example Usage ---
if __name__ == "__main__":
    # Check for all dependencies first
    if not all([PILLOW_AVAILABLE, PIEXIF_AVAILABLE, PYTESSERACT_AVAILABLE, STEGANO_AVAILABLE]):
        print("ERROR: Missing one or more required libraries. Please run:")
        print("pip install Pillow piexif pytesseract stegano")
        sys.exit(1)
    
    try:
        # Check if Tesseract engine is installed before proceeding
        pytesseract.get_tesseract_version()
    except Exception:
        print("\nERROR: Tesseract OCR Engine not found.")
        print("Please install Tesseract for your OS (e.g., 'sudo apt install tesseract-ocr') and ensure it's in your system's PATH.")
        sys.exit(1)

    print("=========================================================")
    print("=== Multimedia Image Processing Prototype 🖼️🔬 ===")
    print("=========================================================")
    
    # 1. Create a dummy image for the demo
    demo_img_path = Path("demo_image.png")
    hidden_img_path = Path("hidden_data_image.png")
    
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    draw.text((10, 10), "Devin Project Test Image\nCVE-2025-9999", fill='black', font=font)
    
    # Add dummy EXIF data
    zeroth_ifd = {piexif.ImageIFD.Make: b"Devin Camera"}
    exif_dict = {"0th": zeroth_ifd, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    exif_bytes = piexif.dump(exif_dict)
    img.save(demo_img_path, "png", exif=exif_bytes)
    logger.info(f"Created demo image at {demo_img_path}")
    
    # --- 2. Run the processing tools ---
    processor = ImageProcessor(image_path=demo_img_path)

    # EXIF Data Demo
    print("\n--- Extracting EXIF Data ---")
    exif_data = processor.extract_exif_data()
    if exif_data:
        print(json.dumps(exif_data, indent=2, default=str))

    # OCR Demo
    print("\n--- Extracting Text with OCR ---")
    ocr_text = processor.extract_text_with_ocr()
    if ocr_text:
        print("Extracted Text:")
        print("--------------------")
        print(ocr_text.strip())
        print("--------------------")

    # Steganography Demo
    print("\n--- Hiding and Revealing Data (Steganography) ---")
    secret = "This is a hidden message!"
    if processor.hide_data_steganography(secret, hidden_img_path):
        # Reveal from the newly created image
        revealer = ImageProcessor(image_path=hidden_img_path)
        revealed_message = revealer.reveal_data_steganography()
        if revealed_message:
            print(f"Successfully revealed message: '{revealed_message}'")
            assert secret == revealed_message
    
    # --- Clean up demo files ---
    if demo_img_path.exists(): demo_img_path.unlink()
    if hidden_img_path.exists(): hidden_img_path.unlink()
    logger.info("Cleaned up demo image files.")

    print("\n=========================================================")
    print("=== Image Processing Prototype Complete ===")
    print("=========================================================")
