import math
import ipaddress
import geoip2.database
from datetime import datetime

class GeoEnricher:
    def __init__(self, db_path="data/geoip/GeoLite2-City.mmdb"):
        self.reader = geoip2.database.Reader(db_path)
        # In-memory tracking of consecutive user logins:
        # { "username": {"timestamp": datetime_obj, "lat": float, "lon": float, "city": str, "country": str} }
        self.user_state = {}

    def is_private_ip(self, ip_str):
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            return ip_obj.is_private or ip_obj.is_loopback
        except ValueError:
            return False

    def lookup_ip(self, ip_str):
        """Returns geo metadata. Private IPs default to local base coordinates."""
        if self.is_private_ip(ip_str):
            return {
                "ip": ip_str,
                "city": "Internal Subnet",
                "country": "LAN",
                "iso_code": "LAN",
                "lat": 55.9533,  # Baseline coordinates (Edinburgh)
                "lon": -3.1883,
                "is_private": True
            }

        try:
            response = self.reader.city(ip_str)
            return {
                "ip": ip_str,
                "city": response.city.name or "Unknown",
                "country": response.country.name or "Unknown",
                "iso_code": response.country.iso_code or "XX",
                "lat": response.location.latitude or 0.0,
                "lon": response.location.longitude or 0.0,
                "is_private": False
            }
        except Exception:
            return {
                "ip": ip_str,
                "city": "Unknown",
                "country": "Unknown",
                "iso_code": "XX",
                "lat": 0.0,
                "lon": 0.0,
                "is_private": False
            }

    @staticmethod
    def haversine_distance_km(lat1, lon1, lat2, lon2):
        """Calculates spherical distance between two GPS coordinates in km."""
        R = 6371.0  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def evaluate_impossible_travel(self, username, current_timestamp_str, current_ip):
        """
        Calculates travel velocity (km/h) relative to the user's prior authentication event.
        Flags impossible travel for speeds exceeding standard aviation cruise speed (> 900 km/h).
        """
        clean_ts = current_timestamp_str.split('+')[0].split('.')[0]
        current_time = datetime.fromisoformat(clean_ts)

        geo = self.lookup_ip(current_ip)
        velocity_kmh = 0.0
        impossible_travel = False
        prev_location = None

        if username and username in self.user_state:
            prev = self.user_state[username]
            time_delta_hours = (current_time - prev["timestamp"]).total_seconds() / 3600.0

            if time_delta_hours > 0.001:  # Guard against division by zero on rapid bursts
                dist_km = self.haversine_distance_km(prev["lat"], prev["lon"], geo["lat"], geo["lon"])
                velocity_kmh = dist_km / time_delta_hours
                if velocity_kmh > 900.0 and dist_km > 200.0:
                    impossible_travel = True
            prev_location = f"{prev['city']}, {prev['country']}"

        # Update cache for public IP authentications
        if username and not geo["is_private"]:
            self.user_state[username] = {
                "timestamp": current_time,
                "lat": geo["lat"],
                "lon": geo["lon"],
                "city": geo["city"],
                "country": geo["country"]
            }

        return {
            "geo": geo,
            "velocity_kmh": round(velocity_kmh, 2),
            "impossible_travel": impossible_travel,
            "prev_location": prev_location
        }

if __name__ == "__main__":
    enricher = GeoEnricher()
    
    # Event 1: User logs in from London, UK
    t1 = "2026-11-09T10:00:00.000+0000"
    ip1 = "81.2.69.142"
    res1 = enricher.evaluate_impossible_travel("jsmith", t1, ip1)
    print(f"[Event 1] User: jsmith | Location: {res1['geo']['city']}, {res1['geo']['country']}")

    # Event 2: User logs in 45 minutes later from Tokyo, Japan
    t2 = "2026-11-09T10:45:00.000+0000"
    ip2 = "133.242.18.1"
    res2 = enricher.evaluate_impossible_travel("jsmith", t2, ip2)
    print(f"[Event 2] User: jsmith | Location: {res2['geo']['city']}, {res2['geo']['country']}")
    print(f"Velocity: {res2['velocity_kmh']} km/h | Impossible Travel Flag: {res2['impossible_travel']}")
