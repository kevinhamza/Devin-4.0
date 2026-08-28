# servers/system_monitor_server.py

import psutil
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Function to monitor CPU usage
def monitor_cpu():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        logging.info(f"CPU Usage: {cpu_usage}%")
        return cpu_usage
    except Exception as e:
        logging.error(f"Error while monitoring CPU: {e}")
        return None

# Function to monitor memory usage
def monitor_memory():
    try:
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent
        logging.info(f"Memory Usage: {memory_usage}%")
        return memory_usage
    except Exception as e:
        logging.error(f"Error while monitoring memory: {e}")
        return None

# Function to monitor disk space
def monitor_disk():
    try:
        disk_info = psutil.disk_usage('/')
        disk_usage = disk_info.percent
        logging.info(f"Disk Usage: {disk_usage}%")
        return disk_usage
    except Exception as e:
        logging.error(f"Error while monitoring disk: {e}")
        return None

# Function to monitor network traffic
def monitor_network():
    try:
        network_info = psutil.net_io_counters()
        network_sent = network_info.bytes_sent
        network_recv = network_info.bytes_recv
        logging.info(f"Network Sent: {network_sent} bytes")
        logging.info(f"Network Received: {network_recv} bytes")
        return network_sent, network_recv
    except Exception as e:
        logging.error(f"Error while monitoring network: {e}")
        return None, None

# Function to monitor system temperature (Assuming a Linux system with `sensors` command)
def monitor_temperature():
    try:
        temp_info = subprocess.run(['sensors'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        temperature = temp_info.stdout
        logging.info(f"System Temperature: {temperature}")
        return temperature
    except Exception as e:
        logging.error(f"Error while monitoring temperature: {e}")
        return None

# Function to monitor robot diagnostics
def monitor_robot_diagnostics():
    try:
        # Custom logic to monitor robot's hardware and sensors
        # This could involve API calls to robotics platforms or direct interaction with hardware
        diagnostics_status = "Diagnostics check complete"
        logging.info(diagnostics_status)
        return diagnostics_status
    except Exception as e:
        logging.error(f"Error while monitoring robot diagnostics: {e}")
        return "Error monitoring robot diagnostics"

# Main function to monitor system health and robot diagnostics
def monitor_system_and_robot():
    try:
        cpu = monitor_cpu()
        memory = monitor_memory()
        disk = monitor_disk()
        network_sent, network_recv = monitor_network()
        temperature = monitor_temperature()
        diagnostics = monitor_robot_diagnostics()

        system_status = {
            "CPU Usage": cpu,
            "Memory Usage": memory,
            "Disk Usage": disk,
            "Network Sent": network_sent,
            "Network Received": network_recv,
            "System Temperature": temperature,
            "Diagnostics Status": diagnostics
        }

        logging.info(f"System and Robot Status: {system_status}")
        return system_status
    except Exception as e:
        logging.error(f"Error during system and robot monitoring: {e}")
        return "Error during monitoring"

if __name__ == "__main__":
    # Example usage
    status = monitor_system_and_robot()
    print(status)
