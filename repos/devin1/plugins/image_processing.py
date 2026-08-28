"""
plugins/image_processing.py
---------------------------
Provides image enhancement capabilities including resizing, filtering,
edge detection, and color adjustments using OpenCV and PIL.
"""

import cv2
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os

class ImageProcessing:
    """
    A class providing advanced image enhancement and transformation capabilities.
    """

    def __init__(self, save_dir="output_images"):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def resize_image(self, image_path, width, height, output_name="resized_image.jpg"):
        """
        Resizes an image to the specified width and height.

        Args:
            image_path (str): Path to the input image.
            width (int): Desired width.
            height (int): Desired height.
            output_name (str): Name for the output file.

        Returns:
            str: Path to the resized image.
        """
        try:
            img = cv2.imread(image_path)
            resized_img = cv2.resize(img, (width, height))
            output_path = os.path.join(self.save_dir, output_name)
            cv2.imwrite(output_path, resized_img)
            return output_path
        except Exception as e:
            return f"Error resizing image: {e}"

    def apply_filter(self, image_path, filter_type="BLUR", output_name="filtered_image.jpg"):
        """
        Applies a filter to the image.

        Args:
            image_path (str): Path to the input image.
            filter_type (str): Type of filter ('BLUR', 'SHARPEN', 'EDGE_ENHANCE').
            output_name (str): Name for the output file.

        Returns:
            str: Path to the filtered image.
        """
        try:
            img = Image.open(image_path)
            filters = {
                "BLUR": ImageFilter.BLUR,
                "SHARPEN": ImageFilter.SHARPEN,
                "EDGE_ENHANCE": ImageFilter.EDGE_ENHANCE
            }
            img_filtered = img.filter(filters.get(filter_type, ImageFilter.BLUR))
            output_path = os.path.join(self.save_dir, output_name)
            img_filtered.save(output_path)
            return output_path
        except Exception as e:
            return f"Error applying filter: {e}"

    def adjust_brightness(self, image_path, factor, output_name="brightness_adjusted.jpg"):
        """
        Adjusts the brightness of an image.

        Args:
            image_path (str): Path to the input image.
            factor (float): Brightness factor (1.0 = original, >1.0 = brighter, <1.0 = darker).
            output_name (str): Name for the output file.

        Returns:
            str: Path to the brightness-adjusted image.
        """
        try:
            img = Image.open(image_path)
            enhancer = ImageEnhance.Brightness(img)
            img_bright = enhancer.enhance(factor)
            output_path = os.path.join(self.save_dir, output_name)
            img_bright.save(output_path)
            return output_path
        except Exception as e:
            return f"Error adjusting brightness: {e}"

    def detect_edges(self, image_path, output_name="edges_detected.jpg"):
        """
        Detects edges in an image using the Canny edge detection method.

        Args:
            image_path (str): Path to the input image.
            output_name (str): Name for the output file.

        Returns:
            str: Path to the edge-detected image.
        """
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            edges = cv2.Canny(img, 100, 200)
            output_path = os.path.join(self.save_dir, output_name)
            cv2.imwrite(output_path, edges)
            return output_path
        except Exception as e:
            return f"Error detecting edges: {e}"

    def convert_to_grayscale(self, image_path, output_name="grayscale_image.jpg"):
        """
        Converts an image to grayscale.

        Args:
            image_path (str): Path to the input image.
            output_name (str): Name for the output file.

        Returns:
            str: Path to the grayscale image.
        """
        try:
            img = cv2.imread(image_path)
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            output_path = os.path.join(self.save_dir, output_name)
            cv2.imwrite(output_path, gray_img)
            return output_path
        except Exception as e:
            return f"Error converting to grayscale: {e}"

if __name__ == "__main__":
    # Example usage
    processor = ImageProcessing()
    print(processor.resize_image("sample.jpg", 800, 600))
    print(processor.apply_filter("sample.jpg", filter_type="SHARPEN"))
    print(processor.adjust_brightness("sample.jpg", factor=1.5))
    print(processor.detect_edges("sample.jpg"))
    print(processor.convert_to_grayscale("sample.jpg"))
