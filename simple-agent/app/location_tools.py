# app/location_tools.py
import json
import os
import urllib.parse
import urllib.request

def _get_api_key() -> str:
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("GOOGLE_MAPS_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        break
    if not key:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set.")
    return key

def geocode_address(address: str) -> str:
    """Convert a human-readable location or address into geographic coordinates (latitude and longitude).
    
    Args:
        address: The address or city name to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'San Francisco, CA').
    """
    try:
        api_key = _get_api_key()
        encoded_address = urllib.parse.quote(address.strip())
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        status = data.get("status")
        if status != "OK" or not data.get("results"):
            return f"Geocoding failed for address '{address}'. Status: {status}"
            
        first_result = data["results"][0]
        formatted_address = first_result.get("formatted_address", address)
        location = first_result["geometry"]["location"]
        lat = location["lat"]
        lng = location["lng"]
        
        return (
            f"Location: {formatted_address}\n"
            f"Latitude: {lat}\n"
            f"Longitude: {lng}"
        )
    except Exception as e:
        return f"Error during geocoding: {e}"

def search_nearby_places(latitude: float, longitude: float, place_type: str = "supermarket", radius_meters: float = 1500.0) -> str:
    """Find nearby places of a specific type (e.g., supermarket, grocery_store, restaurant) near given coordinates.
    
    Args:
        latitude: The center latitude coordinate (e.g., 37.7749).
        longitude: The center longitude coordinate (e.g., -122.4194).
        place_type: Type of place to search for (e.g., 'supermarket', 'grocery_store', 'restaurant', 'bakery').
        radius_meters: Search radius in meters (default: 1500.0).
    """
    try:
        api_key = _get_api_key()
        url = "https://places.googleapis.com/v1/places:searchNearby"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
        }
        
        payload = {
            "includedTypes": [place_type.strip().lower()],
            "maxResultCount": 5,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": float(latitude),
                        "longitude": float(longitude)
                    },
                    "radius": float(radius_meters)
                }
            }
        }
        
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        places = data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m of ({latitude}, {longitude})."
            
        results = []
        for place in places:
            display_name = place.get("displayName", {}).get("text", "Unknown Name")
            address = place.get("formattedAddress", "N/A")
            loc = place.get("location", {})
            lat = loc.get("latitude", "N/A")
            lng = loc.get("longitude", "N/A")
            
            results.append(
                f"Name: {display_name}\n"
                f"Address: {address}\n"
                f"Location: ({lat}, {lng})"
            )
            
        return f"Found {len(results)} nearby '{place_type}' location(s):\n\n" + "\n---\n".join(results)
    except Exception as e:
        return f"Error searching nearby places: {e}"
