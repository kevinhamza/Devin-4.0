# # Devin/modules/robotics/object_detection.py
# # Purpose: Provides object detection capabilities using a pre-trained
# #          deep learning model (YOLO) to identify objects in an image.

# import logging
# from dataclasses import dataclass
# from typing import List, Tuple, Dict, Optional
# import os

# # --- Dependency Installation Notes ---
# # This module requires several libraries for real functionality:
# #
# # 1. OpenCV: For image processing and loading the DNN model.
# #    pip install opencv-python
# #
# # 2. NumPy: For numerical operations on image data.
# #    pip install numpy
# #
# # --- Model Files ---
# # This module also requires pre-trained model files for YOLOv3.
# # You can download them from the official YOLO website or other sources.
# # The three required files are:
# # 1. yolov3.weights - The pre-trained weights.
# # 2. yolov3.cfg - The model configuration file.
# # 3. coco.names - A text file with the names of the 80 objects the model can detect.

# try:
#     import cv2
#     import numpy as np
#     CV_LIBS_AVAILABLE = True
# except ImportError:
#     CV_LIBS_AVAILABLE = False
#     cv2 = None
#     np = None
#     logger.error("Required libraries not found! Please run: 'pip install opencv-python numpy'. This module will be non-functional.")

# # Configure basic logging
# logger = logging.getLogger("ObjectDetection")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class Detection:
#     """Represents a single detected object in an image."""
#     label: str
#     confidence: float
#     # Bounding box in format (x, y, width, height) where x,y is the top-left corner
#     bounding_box: Tuple[int, int, int, int]
#     class_id: int

# class ObjectDetector:
#     """
#     Uses a pre-trained YOLO model to detect objects in images.
#     """

#     def __init__(self, model_weights_path: str, model_config_path: str, labels_path: str):
#         """
#         Initializes the detector by loading the YOLO model and class labels.

#         Args:
#             model_weights_path (str): Path to the .weights file.
#             model_config_path (str): Path to the .cfg file.
#             labels_path (str): Path to the .names file containing class labels.
#         """
#         if not CV_LIBS_AVAILABLE:
#             self.net = None
#             self.labels = []
#             logger.error("ObjectDetector could not be initialized due to missing libraries.")
#             return

#         logger.info("Initializing ObjectDetector...")
#         if not all(os.path.exists(p) for p in [model_weights_path, model_config_path, labels_path]):
#             self.net = None
#             logger.error("Model files not found! Please provide correct paths to YOLOv3 .weights, .cfg, and .names files.")
#             return

#         # Load class labels
#         with open(labels_path, 'r') as f:
#             self.labels = [line.strip() for line in f.readlines()]
        
#         # Load the neural network from disk
#         logger.info(f"Loading YOLO model from '{model_weights_path}' and '{model_config_path}'...")
#         self.net = cv2.dnn.readNetFromDarknet(model_config_path, model_weights_path)
        
#         # Get the names of the output layers
#         layer_names = self.net.getLayerNames()
#         try:
#             # Newer OpenCV versions have a different way to get output layer names
#             self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
#         except TypeError:
#              # Older OpenCV versions
#              self.output_layers = [layer_names[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

#         logger.info("YOLO model loaded successfully.")

#     def detect_objects(self, image: np.ndarray, confidence_threshold: float = 0.5, nms_threshold: float = 0.4) -> List[Detection]:
#         """
#         Detects objects in a given image.

#         Args:
#             image (np.ndarray): The input image in OpenCV format (BGR).
#             confidence_threshold (float): Minimum probability to filter weak detections.
#             nms_threshold (float): Threshold for non-maxima suppression to remove redundant boxes.

#         Returns:
#             List[Detection]: A list of detected objects.
#         """
#         if self.net is None:
#             logger.error("Model not loaded. Cannot perform detection.")
#             return []

#         height, width, _ = image.shape

#         # 1. Pre-process the image and create a "blob"
#         # YOLO requires a specific input format (416x416 is common)
#         blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
#         self.net.setInput(blob)
        
#         # 2. Perform a forward pass (inference) through the network
#         logger.info("Performing forward pass through the network...")
#         layer_outputs = self.net.forward(self.output_layers)
        
#         # 3. Post-process the output
#         boxes, confidences, class_ids = self._postprocess_output(layer_outputs, width, height, confidence_threshold)
        
#         # 4. Apply Non-Maximal Suppression (NMS) to remove redundant overlapping boxes
#         indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)
        
#         detections = []
#         if len(indices) > 0:
#             for i in indices.flatten():
#                 detections.append(Detection(
#                     label=self.labels[class_ids[i]],
#                     confidence=confidences[i],
#                     bounding_box=boxes[i],
#                     class_id=class_ids[i]
#                 ))
        
#         logger.info(f"Detection complete. Found {len(detections)} objects after NMS.")
#         return detections

#     def _postprocess_output(self, layer_outputs: List[np.ndarray], width: int, height: int, confidence_threshold: float) -> Tuple[List, List, List]:
#         """Parses the raw output from the YOLO network layers."""
#         boxes, confidences, class_ids = [], [], []
        
#         for output in layer_outputs:
#             for detection in output:
#                 scores = detection[5:]
#                 class_id = np.argmax(scores)
#                 confidence = scores[class_id]
                
#                 if confidence > confidence_threshold:
#                     # Scale bounding box coordinates back to the original image size
#                     box = detection[0:4] * np.array([width, height, width, height])
#                     (center_x, center_y, box_width, box_height) = box.astype("int")
                    
#                     # Use the center coordinates to derive the top-left corner
#                     x = int(center_x - (box_width / 2))
#                     y = int(center_y - (box_height / 2))
                    
#                     boxes.append([x, y, int(box_width), int(box_height)])
#                     confidences.append(float(confidence))
#                     class_ids.append(class_id)
                    
#         return boxes, confidences, class_ids

#     @staticmethod
#     def draw_detections(image: np.ndarray, detections: List[Detection]) -> np.ndarray:
#         """Draws bounding boxes and labels on an image."""
#         img_copy = image.copy()
#         colors = np.random.uniform(0, 255, size=(len(detections) * 3, 3)).reshape(len(detections)*3, 3) # Generate some colors
        
#         for i, detection in enumerate(detections):
#             label = detection.label
#             confidence = detection.confidence
#             x, y, w, h = detection.bounding_box
#             color = colors[detection.class_id]
            
#             # Draw the bounding box
#             cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, 2)
            
#             # Draw the label text
#             text = f"{label}: {confidence:.2f}"
#             cv2.putText(img_copy, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
#         return img_copy


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Robotics Object Detection Prototype 🖼️👁️ ===")
#     print("=========================================================")

#     if not CV_LIBS_AVAILABLE:
#         print("\nOpenCV and NumPy libraries not found. Please install them to run the demo.")
#     else:
#         # --- IMPORTANT ---
#         # Define paths to your downloaded YOLOv3 model files.
#         # These files are not included. You must download them yourself.
#         # Search for "YOLOv3 weights" to find sources.
#         MODEL_DIR = "./yolo_model"
#         WEIGHTS_PATH = os.path.join(MODEL_DIR, "yolov3.weights")
#         CONFIG_PATH = os.path.join(MODEL_DIR, "yolov3.cfg")
#         LABELS_PATH = os.path.join(MODEL_DIR, "coco.names")
        
#         # Check if model files exist before proceeding
#         if not os.path.exists(WEIGHTS_PATH):
#             print(f"\nERROR: YOLO model files not found in '{MODEL_DIR}' directory.")
#             print("Please download 'yolov3.weights', 'yolov3.cfg', and 'coco.names' and place them there.")
#         else:
#             # 1. Initialize the detector
#             detector = ObjectDetector(
#                 model_weights_path=WEIGHTS_PATH,
#                 model_config_path=CONFIG_PATH,
#                 labels_path=LABELS_PATH
#             )
            
#             # 2. Load a sample image for detection
#             # Create a dummy image if one doesn't exist
#             SAMPLE_IMAGE_PATH = "sample_detection_image.jpg"
#             if not os.path.exists(SAMPLE_IMAGE_PATH):
#                  # Create a simple image with a green square
#                  dummy_image = np.zeros((600, 800, 3), dtype="uint8")
#                  cv2.rectangle(dummy_image, (200, 200), (400, 400), (0, 255, 0), -1)
#                  cv2.putText(dummy_image, "Image for testing", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
#                  cv2.imwrite(SAMPLE_IMAGE_PATH, dummy_image)
#                  print(f"Created a dummy image at '{SAMPLE_IMAGE_PATH}' for the demo.")
            
#             print(f"\nLoading image from '{SAMPLE_IMAGE_PATH}'...")
#             image_to_detect = cv2.imread(SAMPLE_IMAGE_PATH)

#             # 3. Perform detection
#             if image_to_detect is not None and detector.net is not None:
#                 detected_objects = detector.detect_objects(image_to_detect)
                
#                 # 4. Print results
#                 print(f"\n--- Detection Results ---")
#                 if detected_objects:
#                     for obj in detected_objects:
#                         print(f"  - Found '{obj.label}' with {obj.confidence:.2%} confidence at {obj.bounding_box}")
#                 else:
#                     # The dummy image won't have COCO objects, so this is expected for the first run.
#                     print("  No objects from the COCO dataset were detected in the image.")
                
#                 # 5. Draw results on the image and save it
#                 output_image = detector.draw_detections(image_to_detect, detected_objects)
#                 OUTPUT_IMAGE_PATH = "detection_output.jpg"
#                 cv2.imwrite(OUTPUT_IMAGE_PATH, output_image)
#                 print(f"\nOutput image with detections drawn has been saved to '{OUTPUT_IMAGE_PATH}'")

#     print("\n=========================================================")
#     print("=== Object Detection Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/robotics/object_detection.py
# Purpose: Provides state-of-the-art object detection capabilities using the
#          'ultralytics' library with pre-trained YOLO models.

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from pathlib import Path

try:
    import cv2
    import numpy as np
    from ultralytics import YOLO
    from modules.robotics.sensor_integration import Camera
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("ObjectDetection")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class Detection:
    """Represents a single detected object in an image."""
    label: str
    confidence: float
    # Bounding box in format (x_min, y_min, x_max, y_max)
    bounding_box: Tuple[int, int, int, int]
    class_id: int

class ObjectDetector:
    """
    Uses a pre-trained YOLO model from the 'ultralytics' library to detect objects.
    """
    def __init__(self, model_name: str = 'yolov8n.pt'):
        """
        Initializes the detector by loading a YOLO model.
        The model will be downloaded automatically on first use.

        Args:
            model_name (str): The name of the YOLO model to use (e.g., 'yolov8n.pt', 'yolov9c.pt').
        """
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        logger.info(f"Initializing ObjectDetector with YOLO model: '{model_name}'...")
        try:
            self.model = YOLO(model_name)
            logger.info("YOLO model loaded successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model. Check your internet connection or model name. Error: {e}")

    def detect_objects(self, image: np.ndarray, confidence_threshold: float = 0.5) -> List[Detection]:
        """
        Detects objects in a given image.

        Args:
            image (np.ndarray): The input image in OpenCV format (BGR).
            confidence_threshold (float): Minimum probability to filter weak detections.

        Returns:
            List[Detection]: A list of detected objects.
        """
        logger.info("Performing object detection...")
        # The ultralytics library handles all pre/post-processing
        results = self.model(image, conf=confidence_threshold, verbose=False)
        
        detections = []
        # The result object contains all detection information
        for res in results:
            for box in res.boxes:
                class_id = int(box.cls[0])
                detections.append(Detection(
                    label=res.names[class_id],
                    confidence=float(box.conf[0]),
                    bounding_box=tuple(np.array(box.xyxy[0], dtype=int)),
                    class_id=class_id
                ))
        
        logger.info(f"Detection complete. Found {len(detections)} objects.")
        return detections

    def draw_detections(self, image: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Draws bounding boxes and labels on an image."""
        img_copy = image.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bounding_box
            label = f"{det.label}: {det.confidence:.2f}"
            
            # Simple color hashing based on class ID for consistent colors
            color = ((det.class_id * 50) % 255, (det.class_id * 90) % 255, (det.class_id * 120) % 255)
            
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img_copy, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
        return img_copy

# --- High-Level Workflow ---
def detect_objects_in_live_view(detector: ObjectDetector, camera: Camera) -> Optional[List[Detection]]:
    """A complete workflow to capture an image and run detection."""
    logger.info("--- Starting live view detection workflow ---")
    if not camera.is_active:
        if not camera.connect():
            logger.error("Could not connect to camera for live view.")
            return None
    
    # Allow camera to auto-adjust
    time.sleep(1)
    
    frame = camera.read_data()
    if frame is None:
        logger.error("Failed to capture frame from camera.")
        return None
    
    # Save the original capture for reference
    cv2.imwrite("live_capture_original.jpg", frame)
    logger.info("Original live frame saved to 'live_capture_original.jpg'")

    detections = detector.detect_objects(frame)
    
    # Save the image with detections drawn on it
    output_image = detector.draw_detections(frame, detections)
    output_path = "live_detection_output.jpg"
    cv2.imwrite(output_path, output_image)
    logger.info(f"Output image with detections saved to '{output_path}'")
    
    return detections

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Object Detection (Live YOLO Demo) 🖼️👁️ ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing. Error: {_import_error}")
        print("Please run: 'pip install ultralytics opencv-python numpy'")
    else:
        try:
            # --- 1. Initialize the detector and the camera sensor ---
            # The model will be downloaded automatically on the first run.
            detector = ObjectDetector(model_name='yolov8n.pt')
            camera = Camera(sensor_id="system_webcam")

            # --- 2. Run the full capture-and-detect workflow ---
            detected_objects = detect_objects_in_live_view(detector, camera)

            # --- 3. Print results ---
            print("\n--- Detection Results from Live Webcam Feed ---")
            if detected_objects:
                for obj in detected_objects:
                    print(f"  - Found '{obj.label}' with {obj.confidence:.2%} confidence.")
            elif detected_objects == []:
                 print("  No objects were detected in the captured image.")
            else:
                print("  Detection workflow failed.")

        except (ImportError, RuntimeError, FileNotFoundError) as e:
            logger.error(f"Demo failed. Do you have a webcam connected? Error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        finally:
            if 'camera' in locals() and camera.is_active:
                camera.disconnect()

    print("\n=========================================================")
    print("=== Object Detection Prototype Complete ===")
    print("=========================================================")
