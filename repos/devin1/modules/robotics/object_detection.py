"""
Object Detection Module
=======================
AI-powered object detection for robotics applications, leveraging deep learning models.
"""

import cv2
import numpy as np
import logging
from modules.utils.ai_memory import MemoryManager


class ObjectDetectionConfig:
    def __init__(self, model_path: str, config_path: str, labels_path: str, confidence_threshold: float = 0.5):
        """
        Configuration for object detection.

        Args:
            model_path (str): Path to the pre-trained model.
            config_path (str): Path to the model configuration file.
            labels_path (str): Path to the labels file.
            confidence_threshold (float): Minimum confidence threshold for detections.
        """
        self.model_path = model_path
        self.config_path = config_path
        self.labels_path = labels_path
        self.confidence_threshold = confidence_threshold


class ObjectDetector:
    def __init__(self, config: ObjectDetectionConfig):
        """
        Initializes the object detection module with the given configuration.

        Args:
            config (ObjectDetectionConfig): Configuration for object detection.
        """
        logging.info("Initializing Object Detector...")
        self.config = config
        self.net = cv2.dnn.readNetFromDarknet(config.config_path, config.model_path)
        self.layer_names = self.net.getLayerNames()
        self.output_layers = [self.layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        with open(config.labels_path, "r") as file:
            self.labels = file.read().strip().split("\n")
        self.memory = MemoryManager()

    def detect_objects(self, image: np.ndarray) -> list:
        """
        Detects objects in a given image.

        Args:
            image (np.ndarray): Input image for detection.

        Returns:
            list: List of detected objects with their labels, confidence scores, and bounding boxes.
        """
        logging.info("Performing object detection...")
        height, width = image.shape[:2]
        blob = cv2.dnn.blobFromImage(image, scalefactor=1/255.0, size=(416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)

        boxes, confidences, class_ids = [], [], []
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > self.config.confidence_threshold:
                    center_x, center_y, w, h = (detection[0:4] * np.array([width, height, width, height])).astype("int")
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, int(w), int(h)])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.config.confidence_threshold, 0.4)
        detected_objects = []
        for i in indices.flatten():
            detected_objects.append({
                "label": self.labels[class_ids[i]],
                "confidence": confidences[i],
                "box": boxes[i]
            })
        logging.info(f"Detected {len(detected_objects)} objects.")
        self.memory.save_detection_results(detected_objects)
        return detected_objects

    @staticmethod
    def draw_detections(image: np.ndarray, detections: list) -> np.ndarray:
        """
        Draws the detections on the image.

        Args:
            image (np.ndarray): The original image.
            detections (list): List of detected objects.

        Returns:
            np.ndarray: Image with drawn detections.
        """
        logging.info("Drawing detections on image...")
        for detection in detections:
            x, y, w, h = detection["box"]
            label = detection["label"]
            confidence = detection["confidence"]
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, f"{label}: {confidence:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return image


# Example Usage
if __name__ == "__main__":
    config = ObjectDetectionConfig(
        model_path="yolov4.weights",
        config_path="yolov4.cfg",
        labels_path="coco.names",
        confidence_threshold=0.5
    )
    detector = ObjectDetector(config)

    # Load an example image
    input_image = cv2.imread("test_image.jpg")
    detections = detector.detect_objects(input_image)
    output_image = detector.draw_detections(input_image, detections)

    # Display the output
    cv2.imshow("Object Detection", output_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
