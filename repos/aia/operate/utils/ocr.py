import pytesseract
from PIL import Image
import os
from modules.error_handling import ErrorHandling


class OCRUtility:
    """
    Utility for Optical Character Recognition (OCR) operations.
    """

    def __init__(self, tess_path=None):
        """
        Initialize the OCR Utility with optional Tesseract binary path.
        :param tess_path: Path to the Tesseract binary (if not in system PATH).
        """
        self.error_handler = ErrorHandling()
        if tess_path:
            pytesseract.pytesseract.tesseract_cmd = tess_path
        print(f"Tesseract Path: {pytesseract.pytesseract.tesseract_cmd}")

    def extract_text(self, image_path):
        """
        Extract text from an image using OCR.
        :param image_path: Path to the image file.
        :return: Extracted text or None on failure.
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")

            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            print(f"Extracted text from {image_path}: \n{text}")
            return text
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to extract text.")
            return None

    def extract_text_from_region(self, image_path, region):
        """
        Extract text from a specific region in an image.
        :param image_path: Path to the image file.
        :param region: Tuple (left, upper, right, lower) specifying the region.
        :return: Extracted text or None on failure.
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")

            image = Image.open(image_path)
            cropped_image = image.crop(region)
            text = pytesseract.image_to_string(cropped_image)
            print(f"Extracted text from region in {image_path}: \n{text}")
            return text
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to extract text from region.")
            return None

    def save_text_to_file(self, text, output_file):
        """
        Save extracted text to a file.
        :param text: Extracted text to save.
        :param output_file: File to save the text to.
        """
        try:
            with open(output_file, "w") as file:
                file.write(text)
            print(f"Text saved to {output_file}")
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to save text to file.")

    def list_supported_languages(self):
        """
        List supported languages for OCR.
        :return: List of supported languages.
        """
        try:
            languages = pytesseract.get_languages(config='')
            print(f"Supported OCR languages: {languages}")
            return languages
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to list supported languages.")
            return []


if __name__ == "__main__":
    ocr = OCRUtility()

    # Example usage: Extract text from an image
    text = ocr.extract_text("example_image.png")

    # Example usage: Extract text from a specific region
    region = (50, 50, 300, 300)
    ocr.extract_text_from_region("example_image.png", region)

    # Example usage: Save extracted text to a file
    if text:
        ocr.save_text_to_file(text, "output_text.txt")

    # Example: List supported OCR languages
    ocr.list_supported_languages()
