# Devin AGI - Backend Server API Documentation

This document provides details on the primary REST API endpoints for Devin's backend services.

---

## 1. Analytics Server

**Base URL:** `http://localhost:5004`

### Log an Event
- **Endpoint:** `/log`
- **Method:** `POST`
- **Description:** Logs a single, timestamped event to the in-memory analytics database.
- **Request Body (JSON):**
  ```json
  {
    "event_type": "cpu_usage",
    "value": 75.5
  }
  ```

  - **Response:**
      - `200 OK`: `{"status": "success"}`
      - `400 Bad Request`: If `event_type` is missing or `value` is not a number.

### Get Timeseries Data

  - **Endpoint:** `/data`
  - **Method:** `GET`
  - **Description:** Retrieves aggregated, time-series data for all logged events within a specified period.
  - **Query Parameters:**
      - `period` (string, required): The time window to retrieve. Examples: `5m`, `1h`, `3d`.
  - **Example Request:** `GET /data?period=1h`
  - **Success Response (JSON):**
    ```json
    {
      "cpu_usage": [
        { "timestamp": "2025-09-03T21:50:00Z", "value": 75.5 },
        { "timestamp": "2025-09-03T21:51:00Z", "value": 78.2 }
      ],
      "api_calls": [
        { "timestamp": "2025-09-03T21:50:15Z", "value": 120 }
      ]
    }
    ```

-----

## 2\. Cloud Integration Server

**Base URL:** `http://localhost:5002`

### List Resources

  - **Endpoint:** `/<provider>/<resource_type>`
  - **Method:** `GET`
  - **Description:** Lists all resources of a given type from a specified cloud provider in a normalized format.
  - **URL Parameters:**
      - `provider`: The cloud provider. One of `aws`, `gcp`, `azure`.
      - `resource_type`: The type of resource. One of `vms`, `buckets`, `databases`.
  - **Example Request:** `GET /aws/vms`
  - **Success Response (JSON):**
    ```json
    [
      {
        "name": "WebServer-Prod",
        "provider": "AWS",
        "provider_id": "i-01a2b3c4d5e6f7g8h",
        "public_ip": "54.123.45.67",
        "resource_type": "VIRTUAL_MACHINE",
        "status": "running",
        "tags": { "Name": "WebServer-Prod" },
        "details": { "instance_type": "t2.micro" }
      }
    ]
    ```

-----

## 3\. Mobile Integration Server

**Base URL:** `http://localhost:5006`

### List Connected Devices

  - **Endpoint:** `/devices`
  - **Method:** `GET`
  - **Description:** Returns a list of all Android devices connected via ADB.
  - **Success Response (JSON):**
    ```json
    [
      {
        "serial": "emulator-5554",
        "status": "device"
      }
    ]
    ```

### Execute Shell Command

  - **Endpoint:** `/shell`
  - **Method:** `POST`
  - **Description:** Executes an ADB shell command on a specific device.
  - **Request Body (JSON):**
    ```json
    {
      "device_id": "emulator-5554",
      "command": "getprop ro.product.model"
    }
    ```
  - **Success Response (JSON):**
    ```json
    {
      "output": "Pixel 8 Pro\\n",
      "status": "success"
    }
    ```
  - **Error Response:**
      - `500 Internal Server Error`: If the `adb` command fails.
<!-- end list -->
