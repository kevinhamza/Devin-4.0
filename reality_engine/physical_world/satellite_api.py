# Devin/reality_engine/physical_world/satellite_api.py
# Purpose: A toolkit for interacting with geolocation and satellite data APIs,
#          providing geocoding, IP location, and satellite tracking.

import logging
import requests
from typing import Optional, Dict, Any

try:
    from geopy.geocoders import Nominatim
    from geopy.location import Location
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("SatelliteAPI")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class SatelliteAPI:
    """
    Provides an interface to various geolocation and satellite tracking services.
    """
    def __init__(self, user_agent: str = "Devin-Geolocation-Client/1.0"):
        if not GEOPY_AVAILABLE:
            raise ImportError("The 'geopy' library is required. 'pip install geopy'")
        
        self.geolocator = Nominatim(user_agent=user_agent)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        logger.info("SatelliteAPI initialized.")

    def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Converts a physical address to latitude and longitude.
        """
        logger.info(f"Geocoding address: '{address}'")
        try:
            location = self.geolocator.geocode(address, timeout=10)
            if location:
                return {"address": location.address, "latitude": location.latitude, "longitude": location.longitude}
            else:
                logger.warning("Address could not be geocoded.")
                return None
        except Exception as e:
            logger.error(f"Geocoding failed: {e}")
            return None

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Converts latitude and longitude coordinates to a physical address.
        """
        logger.info(f"Reverse geocoding coordinates: ({latitude}, {longitude})")
        try:
            location = self.geolocator.reverse((latitude, longitude), timeout=10)
            if location:
                return {"address": location.address, "raw": location.raw}
            else:
                logger.warning("Coordinates could not be reverse geocoded.")
                return None
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
            return None

    def get_iss_location(self) -> Optional[Dict[str, Any]]:
        """
        Gets the current real-time location of the International Space Station (ISS).
        """
        logger.info("Fetching current ISS location...")
        url = "https://api.wheretheiss.at/v1/satellites/25544"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch ISS location: {e}")
            return None

    def geocode_ip_address(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Gets the approximate geolocation of a public IP address.
        """
        logger.info(f"Geolocating IP address: {ip_address}")
        url = f"http://ip-api.com/json/{ip_address}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "fail":
                logger.error(f"Failed to geolocate IP {ip_address}: {data.get('message')}")
                return None
            return data
        except requests.RequestException as e:
            logger.error(f"Failed to fetch IP geolocation data: {e}")
            return None

# --- Example Usage ---
if __name__ == "__main__":
    if not GEOPY_AVAILABLE:
        print("\nERROR: The 'geopy' library is required for this demo.")
        print("Please run: pip install geopy")
    else:
        print("=========================================================")
        print("=== Geolocation & Satellite API Prototype 🛰️🌍 ===")
        print("=========================================================")

        api = SatelliteAPI()

        # --- 1. Geocoding Demo ---
        print("\n--- 1. Geocoding Address ---")
        address_str = "Eiffel Tower, Paris, France"
        location = api.geocode_address(address_str)
        if location:
            print(f"  Address: {address_str}")
            print(f"  Coordinates: (Lat: {location['latitude']:.4f}, Lon: {location['longitude']:.4f})")
            lat, lon = location['latitude'], location['longitude']

            # --- 2. Reverse Geocoding Demo ---
            print("\n--- 2. Reverse Geocoding Coordinates ---")
            address_lookup = api.reverse_geocode(lat, lon)
            if address_lookup:
                print(f"  Coordinates: (Lat: {lat:.4f}, Lon: {lon:.4f})")
                print(f"  Found Address: {address_lookup['address']}")

        # --- 3. ISS Location Demo ---
        print("\n--- 3. Real-time ISS Location ---")
        iss_data = api.get_iss_location()
        if iss_data:
            print(f"  Timestamp: {datetime.fromtimestamp(iss_data['timestamp'])}")
            print(f"  Coordinates: (Lat: {iss_data['latitude']:.4f}, Lon: {iss_data['longitude']:.4f})")
            print(f"  Velocity: {iss_data['velocity']:.2f} km/h")
        
        # --- 4. IP Geolocation Demo ---
        print("\n--- 4. IP Address Geolocation ---")
        ip = "8.8.8.8" # Google's public DNS
        ip_data = api.geocode_ip_address(ip)
        if ip_data:
            print(f"  IP Address: {ip}")
            print(f"  Location: {ip_data.get('city')}, {ip_data.get('country')}")
            print(f"  ISP: {ip_data.get('isp')}")

    print("\n=========================================================")
    print("=== Geolocation API Prototype Complete ===")
    print("=========================================================")
