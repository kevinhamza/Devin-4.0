"""
Image Processing Tools
======================
This module provides advanced image processing and enhancement tools using OpenCV and PIL.
Features include color correction, resizing, filtering, edge detection, and object detection.

Dependencies:
- OpenCV for image processing
- PIL (Pillow) for image manipulation
- NumPy for array-based operations
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

class ImageProcessing:
    """
    A class to handle advanced image processing tasks.
    """

    def __init__(self):
        """
        Initializes the ImageProcessing class.
        """
        self.default_filter = "sharpen"

    @staticmethod
    def load_image(file_path):
        """
        Loads an image from the specified file path.

        Args:
            file_path (str): Path to the image file.

        Returns:
            ndarray: Loaded image in OpenCV format.
        """
        return cv2.imread(file_path)

    @staticmethod
    def save_image(image, file_path):
        """
        Saves the image to the specified file path.

        Args:
            image (ndarray): Image to save.
            file_path (str): Destination file path.
        """
        cv2.imwrite(file_path, image)

    def resize_image(self, image, width, height):
        """
        Resizes the image to the specified dimensions.

        Args:
            image (ndarray): Original image.
            width (int): Desired width.
            height (int): Desired height.

        Returns:
            ndarray: Resized image.
        """
        return cv2.resize(image, (width, height))

    def apply_filter(self, image, filter_type="sharpen"):
        """
        Applies a filter to the image.

        Args:
            image (ndarray): Input image.
            filter_type (str): Type of filter ('blur', 'sharpen', 'edge').

        Returns:
            ndarray: Filtered image.
        """
        filters = {
            "blur": cv2.GaussianBlur(image, (5, 5), 0),
            "sharpen": cv2.filter2D(image, -1, np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])),
            "edge": cv2.Canny(image, 100, 200),
        }
        return filters.get(filter_type.lower(), image)

    def enhance_image(self, image_path, output_path, factor=1.5):
        """
        Enhances the brightness, sharpness, and contrast of an image.

        Args:
            image_path (str): Path to the input image file.
            output_path (str): Path to save the enhanced image.
            factor (float): Enhancement factor (default: 1.5).
        """
        image = Image.open(image_path)
        enhancer = ImageEnhance.Contrast(image)
        enhanced_image = enhancer.enhance(factor)
        enhanced_image.save(output_path)

    def edge_detection(self, image, threshold1=100, threshold2=200):
        """
        Performs edge detection on the image using Canny algorithm.

        Args:
            image (ndarray): Input image.
            threshold1 (int): Lower threshold for edge detection.
            threshold2 (int): Upper threshold for edge detection.

        Returns:
            ndarray: Image with edges detected.
        """
        return cv2.Canny(image, threshold1, threshold2)

    def detect_objects(self, image, model_path, config_path, classes_file):
        """
        Detects objects in the image using a pre-trained DNN model.

        Args:
            image (ndarray): Input image.
            model_path (str): Path to the pre-trained model weights.
            config_path (str): Path to the model configuration file.
            classes_file (str): Path to the file with class labels.

        Returns:
            ndarray: Image with detected objects outlined.
        """
        # Load class labels
        with open(classes_file, "r") as f:
            classes = [line.strip() for line in f.readlines()]

        # Load model
        net = cv2.dnn.readNet(model_path, config_path)

        # Prepare input blob
        blob = cv2.dnn.blobFromImage(image, scalefactor=1/255.0, size=(416, 416), swapRB=True, crop=False)
        net.setInput(blob)

        # Get output layer names
        layer_names = net.getLayerNames()
        output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

        # Forward pass
        detections = net.forward(output_layers)

        # Draw bounding boxes
        h, w = image.shape[:2]
        for output in detections:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    center_x, center_y, width, height = (detection[:4] * np.array([w, h, w, h])).astype(int)
                    x, y = int(center_x - width / 2), int(center_y - height / 2)
                    cv2.rectangle(image, (x, y), (x + width, y + height), (0, 255, 0), 2)
                    cv2.putText(image, f"{classes[class_id]}: {confidence:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return image


# Example usage
if __name__ == "__main__":
    img_processor = ImageProcessing()
    input_image = "input.jpg"
    output_image = "output.jpg"

    # Load image
    img = img_processor.load_image(input_image)

    # Resize
    resized_img = img_processor.resize_image(img, 800, 600)
    img_processor.save_image(resized_img, "resized.jpg")

    # Enhance
    img_processor.enhance_image(input_image, "enhanced.jpg")

    # Edge detection
    edges = img_processor.edge_detection(resized_img)
    img_processor.save_image(edges, "edges.jpg")

    # Object detection (example with YOLOv4 files)
    detected_img = img_processor.detect_objects(resized_img, "yolov4.weights", "yolov4.cfg", "coco.names")
    img_processor.save_image(detected_img, "detected_objects.jpg")
