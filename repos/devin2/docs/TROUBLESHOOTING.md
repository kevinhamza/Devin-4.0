# Devin AGI - Troubleshooting Guide

This guide provides solutions to common problems encountered during setup and operation.

---

### AI & API Key Issues

-   **Problem:** The application fails on startup with `ValueError: API key not provided...` or API calls fail with a 401 Unauthorized error.
-   **Solution:** Devin's AI modules require API keys to be set as environment variables. Ensure you have a `.env` file in the project root or have exported the variables in your shell.
    -   Check for `OPENAI_API_KEY`, `GEMINI_API_KEY`, `PERPLEXITY_API_KEY`.
    -   For threat intelligence, check for `VIRUSTOTAL_API_KEY`.

-   **Problem:** AI responses are slow or inconsistent.
-   **Solution:** The performance of external LLMs can vary.
    -   Run the `tests/performance/benchmark_ai.py` script to get a live performance comparison of the configured providers.
    -   Check your internet connection.
    -   Check the status pages for the respective AI providers (OpenAI, Google AI, etc.) for any ongoing incidents.

---

### Robotics Module Issues

-   **Problem:** The `robotics_tests.py` integration test fails because it cannot find the `yolov8n.pt` model.
-   **Solution:** The `ObjectDetector` module automatically downloads the YOLOv8 model file on its first initialization. This requires an active internet connection. If the download was interrupted, delete the partial `yolov8n.pt` file and run the script again.

-   **Problem:** ROS 2 integration scripts (e.g., `remote_control.py`, `environment_mapping.py`) fail with `ImportError: rclpy not found` or `ros2 command not found`.
-   **Solution:** The ROS 2 integration requires a full ROS 2 installation (e.g., Humble). You must **source the ROS 2 environment** in your terminal before running the script.
    -   Example: `source /opt/ros/humble/setup.bash`

---

### Server & Dependency Issues

-   **Problem:** `pip install` fails on a specific package, especially `torch` or `dlib`.
-   **Solution:** Some Python packages have complex system dependencies.
    -   For `dlib` (used by `face_recognition`), you may need to install `cmake` and a C++ compiler (like `build-essential` on Debian/Ubuntu).
    -   For `torch` (used by YOLO), it's often best to follow the official PyTorch installation guide for your specific OS and GPU (if any).

-   **Problem:** A client script (e.g., `tests/integration/test_cloud_services.py`) fails with `ConnectionRefusedError`.
-   **Solution:** The integration tests and facades require the corresponding backend server to be running.
    -   Before running `test_cloud_services.py`, you must start the `servers/cloud_integration_server.py` in a separate terminal.
    -   The `if __name__ == "__main__"` block in each test script will specify which server(s) need to be running.
