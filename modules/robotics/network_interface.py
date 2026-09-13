# # Devin/modules/robotics/network_interface.py
# # Purpose: Provides a decoupled, intra-robot communication system using a
# #          Publish/Subscribe (Pub/Sub) message bus pattern.

# import logging
# import threading
# import queue
# import time
# from collections import defaultdict
# from typing import Any, Callable, Dict, List

# # Configure basic logging
# logger = logging.getLogger("RoboticsNetwork")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class NetworkInterface:
#     """
#     A thread-safe, singleton Publish/Subscribe message bus for the robotics system.
#     """
#     _instance = None
#     _lock = threading.Lock()

#     def __new__(cls, *args, **kwargs):
#         if not cls._instance:
#             with cls._lock:
#                 if not cls._instance:
#                     cls._instance = super(NetworkInterface, cls).__new__(cls)
#         return cls._instance

#     def __init__(self):
#         # This check ensures __init__ is only run once for the singleton instance
#         if not hasattr(self, '_initialized'):
#             with self._lock:
#                 if not hasattr(self, '_initialized'):
#                     self.subscribers: Dict[str, List[Callable[[Any], None]]] = defaultdict(list)
#                     self.message_queue = queue.Queue()
#                     self.processing_thread: threading.Thread = None
#                     self._stop_event = threading.Event()
#                     self._initialized = True
#                     logger.info("RoboticsNetwork Interface (Singleton) initialized.")

#     def start(self):
#         """Starts the background message processing thread."""
#         if self.processing_thread and self.processing_thread.is_alive():
#             logger.warning("Network interface is already running.")
#             return

#         self._stop_event.clear()
#         self.processing_thread = threading.Thread(target=self._message_processor_loop, daemon=True)
#         self.processing_thread.start()
#         logger.info("Pub/Sub message processor thread started.")

#     def stop(self):
#         """Stops the message processing thread gracefully."""
#         if not self.processing_thread or not self.processing_thread.is_alive():
#             logger.info("Network interface is not running.")
#             return
            
#         logger.info("Stopping network interface...")
#         self.message_queue.put(None) # Sentinel value to stop the loop
#         self.processing_thread.join(timeout=2.0)
#         self._stop_event.set()
#         logger.info("Network interface stopped.")

#     def subscribe(self, topic: str, callback: Callable[[Any], None]):
#         """
#         Subscribes a callback function to a specific topic.

#         Args:
#             topic (str): The topic to subscribe to (e.g., '/sensors/imu').
#             callback (Callable[[Any], None]): The function to call with the message
#                                               when data is published on the topic.
#         """
#         logger.info(f"New subscription for topic '{topic}' by callback '{callback.__name__}'.")
#         self.subscribers[topic].append(callback)

#     def publish(self, topic: str, message: Any):
#         """
#         Publishes a message to a specific topic. This method is non-blocking.

#         Args:
#             topic (str): The topic to publish the message on.
#             message (Any): The data/message payload.
#         """
#         if self._stop_event.is_set():
#             logger.warning("Interface is stopped. Cannot publish.")
#             return
            
#         logger.debug(f"Publishing message to topic '{topic}'.")
#         self.message_queue.put((topic, message))

#     def _message_processor_loop(self):
#         """The background worker that distributes messages to subscribers."""
#         while not self._stop_event.is_set():
#             try:
#                 message_item = self.message_queue.get()
                
#                 # Check for the stop signal
#                 if message_item is None:
#                     break

#                 topic, message = message_item
                
#                 # Find all callbacks subscribed to this topic
#                 if topic in self.subscribers:
#                     logger.debug(f"Distributing message on '{topic}' to {len(self.subscribers[topic])} subscribers.")
#                     for callback in self.subscribers[topic]:
#                         try:
#                             # Execute the callback with the message
#                             callback(message)
#                         except Exception as e:
#                             logger.error(f"Error in subscriber callback '{callback.__name__}' for topic '{topic}': {e}")
#             except Exception as e:
#                  logger.error(f"Error in message processing loop: {e}")


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Robotics Network Interface Prototype 🌐 === ")
#     print("=========================================================")

#     # 1. Get the singleton instance of the network interface and start it
#     bus = NetworkInterface()
#     bus.start()

#     # 2. Define some subscriber callbacks (representing different modules)
#     def vision_processor_subscriber(image_data):
#         """This function would run in a computer vision module."""
#         print(f"  [Vision Processor] Received image frame with timestamp {image_data['timestamp']}. Processing for objects...")

#     def logger_subscriber(data):
#         """This function would run in the data logger module."""
#         print(f"  [Data Logger]      Received image frame with timestamp {data['timestamp']}. Writing to log file...")

#     # 3. Subscribe the callbacks to a topic
#     print("\n--- Subscribing modules to the '/sensors/camera' topic ---")
#     bus.subscribe("/sensors/camera", vision_processor_subscriber)
#     bus.subscribe("/sensors/camera", logger_subscriber)

#     # 4. Define and start a publisher (representing a hardware driver)
#     def camera_publisher(stop_event):
#         """This function simulates a camera driver publishing images."""
#         while not stop_event.is_set():
#             # Simulate capturing an image
#             image_message = {
#                 "timestamp": time.time(),
#                 "format": "bgr8",
#                 "resolution": (1920, 1080),
#                 "data": "<conceptual_numpy_array_bytes>"
#             }
#             print(f"\n[Camera Driver] Publishing new image frame...")
#             bus.publish("/sensors/camera", image_message)
#             time.sleep(2) # Publish at 0.5 Hz

#     print("\n--- Starting a simulated Camera Publisher in a background thread ---")
#     publisher_stop_event = threading.Event()
#     publisher_thread = threading.Thread(target=camera_publisher, args=(publisher_stop_event,), daemon=True)
#     publisher_thread.start()
    
#     # 5. Let the simulation run for a few seconds
#     try:
#         time.sleep(5)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         # 6. Cleanly shut down the system
#         print("\n\n--- Shutting down the system ---")
#         publisher_stop_event.set()
#         publisher_thread.join(timeout=1.0)
#         bus.stop()

#     print("\n=========================================================")
#     print("=== Network Interface Prototype Complete ===")
#     print("=========================================================")








# Devin/modules/robotics/network_interface.py
# Purpose: A functional, high-level wrapper for the ROS 2 communication
#          system, providing a robust Publish/Subscribe message bus.

import logging
import threading
from typing import Any, Callable, Dict, Optional, Type

try:
    # --- ROS 2 Integration ---
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("RoboticsNetwork")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class ROS2Interface:
    """
    A high-level wrapper for a ROS 2 node, providing a simple
    Publish/Subscribe interface for intra-robot communication.
    """
    def __init__(self, node_name: str):
        if not ROS2_AVAILABLE:
            raise ImportError("ROS 2 Python client (rclpy) not found. Please install ROS 2 and source your environment.")
        
        self.node_name = node_name
        self.node: Optional[Node] = None
        self.executor_thread: Optional[threading.Thread] = None
        self._publishers: Dict[str, Any] = {}
        
    def start(self):
        """Initializes the ROS 2 context and starts spinning the node in a background thread."""
        if self.node:
            logger.warning(f"ROS 2 node '{self.node_name}' is already running.")
            return

        def spin_thread():
            logger.info(f"Starting ROS 2 executor spin for node '{self.node_name}'...")
            rclpy.spin(self.node)
            logger.info(f"ROS 2 executor for node '{self.node_name}' has stopped.")
            self.node.destroy_node()

        try:
            if not rclpy.ok():
                rclpy.init()
            self.node = Node(self.node_name)
            self.executor_thread = threading.Thread(target=spin_thread, daemon=True)
            self.executor_thread.start()
            logger.info(f"ROS 2 node '{self.node_name}' started successfully.")
        except Exception as e:
            logger.error(f"Failed to start ROS 2 node: {e}")
            self.node = None

    def stop(self):
        """Shuts down the ROS 2 node and context."""
        if rclpy.ok():
            logger.info(f"Shutting down ROS 2 node '{self.node_name}'...")
            rclpy.shutdown()
            if self.executor_thread:
                self.executor_thread.join(timeout=2.0)
            logger.info("ROS 2 shutdown complete.")

    def subscribe(self, topic: str, msg_type: Type, callback: Callable[[Any], None]):
        """Subscribes a callback function to a specific ROS 2 topic."""
        if not self.node:
            raise RuntimeError("Cannot subscribe: ROS 2 node is not running.")
        
        # Use a reliable QoS for subscribers that shouldn't miss messages
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        self.node.create_subscription(msg_type, topic, callback, qos_profile)
        logger.info(f"Node '{self.node_name}' subscribed to topic '{topic}'.")

    def publish(self, topic: str, msg_type: Type, message: Any):
        """Publishes a message to a specific ROS 2 topic."""
        if not self.node:
            raise RuntimeError("Cannot publish: ROS 2 node is not running.")
        
        # Create and cache publishers for efficiency
        if topic not in self._publishers:
            self._publishers[topic] = self.node.create_publisher(msg_type, topic, 10)
            logger.info(f"Created new publisher for topic '{topic}'.")
            
        self._publishers[topic].publish(message)

# --- Example Usage: A mini ROS 2 application in one script ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Robotics Network (Live ROS 2 Demo) 🌐 ===")
    print("=========================================================")
    
    if not ROS2_AVAILABLE:
        print("\nERROR: ROS 2 (rclpy) not found. This demo requires a sourced ROS 2 environment.")
    else:
        # We need a message type for the demo
        from std_msgs.msg import String

        # --- 1. Define a subscriber callback ---
        def listener_callback(msg):
            """This function is executed whenever a message is received."""
            logger.info(f"[Listener Node] I heard: '{msg.data}'")
        
        talker_node = None
        listener_node = None
        try:
            # --- 2. Create and start two separate ROS 2 nodes ---
            print("\n--- 1. Starting two ROS 2 nodes: 'talker' and 'listener' ---")
            talker_node = ROS2Interface("talker")
            listener_node = ROS2Interface("listener")
            talker_node.start()
            listener_node.start()
            
            # --- 3. Set up the subscription ---
            print("\n--- 2. Subscribing the 'listener' node to the '/chatter' topic ---")
            listener_node.subscribe("/chatter", String, listener_callback)
            
            # --- 4. Start publishing from the 'talker' node ---
            print("\n--- 3. Publishing from the 'talker' node... (Press Ctrl+C to stop) ---")
            count = 0
            while True:
                msg = String()
                msg.data = f"Hello from Devin's ROS 2 talker! Count: {count}"
                talker_node.publish("/chatter", String, msg)
                logger.info(f"[Talker Node] Publishing: '{msg.data}'")
                count += 1
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nUser interrupted. Shutting down nodes.")
        except Exception as e:
            logger.error(f"Demo failed to run: {e}")
        finally:
            # --- 5. Cleanly shut down ---
            # The stop() function shuts down the entire rclpy context, so we only call it once.
            if talker_node:
                talker_node.stop()

    print("\n=========================================================")
    print("=== Robotics Network Demo Complete ===")
    print("=========================================================")
