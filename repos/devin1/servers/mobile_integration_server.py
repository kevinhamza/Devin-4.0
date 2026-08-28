import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# Initialize FastAPI app
app = FastAPI()

# Logger setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MobileIntegrationServer")

# Device Model
class Device(BaseModel):
    device_id: str
    device_type: str  # 'Android' or 'iOS'
    name: str
    os_version: str

# In-memory storage for connected devices
connected_devices = {}

# API to register a device
@app.post("/register")
async def register_device(device: Device):
    if device.device_id in connected_devices:
        raise HTTPException(status_code=400, detail="Device already registered.")
    connected_devices[device.device_id] = device
    logger.info(f"Device registered: {device}")
    return {"message": "Device registered successfully.", "device": device.dict()}

# API to fetch connected devices
@app.get("/devices")
async def list_devices():
    return {"connected_devices": list(connected_devices.values())}

# API to send notification to a device
@app.post("/send-notification")
async def send_notification(device_id: str, message: str):
    if device_id not in connected_devices:
        raise HTTPException(status_code=404, detail="Device not found.")
    device = connected_devices[device_id]
    logger.info(f"Sending notification to {device.name} ({device.device_type}): {message}")
    # Simulate sending notification (placeholder for actual integration)
    return {"message": "Notification sent.", "device": device.dict(), "content": message}

# API to unregister a device
@app.delete("/unregister/{device_id}")
async def unregister_device(device_id: str):
    if device_id not in connected_devices:
        raise HTTPException(status_code=404, detail="Device not found.")
    removed_device = connected_devices.pop(device_id)
    logger.info(f"Device unregistered: {removed_device}")
    return {"message": "Device unregistered successfully.", "device": removed_device.dict()}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "Mobile Integration Server is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
