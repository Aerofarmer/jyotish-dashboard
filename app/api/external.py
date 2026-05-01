"""
External API integrations:
  - OpenCage Geocoder  → city name → (lat, lon, timezone)
  - TimeZoneDB         → (lat, lon) → IANA timezone string
  - Prokerala          → supplementary Panchang data (optional)

All calls have timeouts and graceful fallbacks so the app works offline.
"""
import os
import requests
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim, OpenCage
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import pytz
from functools import lru_cache

OPENCAGE_KEY   = os.getenv("OPENCAGE_API_KEY", "")
TIMEZONEDB_KEY = os.getenv("TIMEZONEDB_API_KEY", "")
PROKERALA_ID   = os.getenv("PROKERALA_CLIENT_ID", "")
PROKERALA_SEC  = os.getenv("PROKERALA_CLIENT_SECRET", "")

_tf = TimezoneFinder()


@lru_cache(maxsize=256)
def geocode_place(place_name: str) -> dict:
    """
    Convert a place name to lat/lon/timezone.
    Priority:  OpenCage API → Nominatim (free fallback)
    Returns dict with keys: lat, lon, timezone, display_name
    """
    # --- Try OpenCage (most accurate) ---
    if OPENCAGE_KEY:
        try:
            gc = OpenCage(OPENCAGE_KEY, timeout=5)
            results = gc.geocode(place_name, exactly_one=True)
            if results:
                lat = results.latitude
                lon = results.longitude
                tz  = _tz_from_coords(lat, lon)
                return {
                    "lat": lat, "lon": lon,
                    "timezone": tz,
                    "display_name": results.address,
                    "source": "OpenCage",
                }
        except (GeocoderTimedOut, GeocoderServiceError, Exception):
            pass

    # --- Fallback: Nominatim (OpenStreetMap, no key needed) ---
    try:
        gc = Nominatim(user_agent="kundli-dashboard/1.0", timeout=5)
        results = gc.geocode(place_name, exactly_one=True, language="en")
        if results:
            lat = results.latitude
            lon = results.longitude
            tz  = _tz_from_coords(lat, lon)
            return {
                "lat": lat, "lon": lon,
                "timezone": tz,
                "display_name": results.address,
                "source": "Nominatim",
            }
    except (GeocoderTimedOut, GeocoderServiceError, Exception):
        pass

    return {"error": f"Could not geocode '{place_name}'"}


def _tz_from_coords(lat: float, lon: float) -> str:
    """
    Get IANA timezone string from coordinates.
    Priority:  timezonefinder (local, offline) → TimeZoneDB API
    """
    # timezonefinder — fast, offline, very accurate
    tz = _tf.timezone_at(lat=lat, lng=lon)
    if tz:
        return tz

    # TimeZoneDB API fallback
    if TIMEZONEDB_KEY:
        try:
            url = "http://api.timezonedb.com/v2.1/get-time-zone"
            params = {
                "key": TIMEZONEDB_KEY, "format": "json",
                "by": "position", "lat": lat, "lng": lon,
            }
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            if data.get("status") == "OK":
                return data.get("zoneName", "UTC")
        except Exception:
            pass

    # Last-resort: guess by longitude offset
    offset_hours = round(lon / 15)
    return f"Etc/GMT{'+' if offset_hours <= 0 else ''}{-offset_hours}"


def get_prokerala_panchang(date_str: str, lat: float, lon: float, tz_str: str) -> dict | None:
    """
    Fetch supplementary Panchang from Prokerala API.
    Returns None if credentials not set or request fails.
    API docs: https://api.prokerala.com/docs
    """
    if not (PROKERALA_ID and PROKERALA_SEC):
        return None

    token = _prokerala_token()
    if not token:
        return None

    try:
        tz = pytz.timezone(tz_str)
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt_local = tz.localize(dt.replace(hour=6))
        datetime_str = dt_local.strftime("%Y-%m-%dT%H:%M:%S%z")

        url = "https://api.prokerala.com/v2/astrology/panchang"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "ayanamsa": 1,          # Lahiri
            "coordinates": f"{lat},{lon}",
            "datetime": datetime_str,
        }
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("data", {})
    except Exception:
        pass

    return None


def _prokerala_token() -> str | None:
    """OAuth2 client credentials token for Prokerala."""
    try:
        resp = requests.post(
            "https://api.prokerala.com/token",
            data={
                "grant_type": "client_credentials",
                "client_id": PROKERALA_ID,
                "client_secret": PROKERALA_SEC,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        pass
    return None


def get_ip_location() -> dict:
    """
    Auto-detect approximate location from the server's public IP.
    Uses ip-api.com (free, no key needed, 45 req/min).
    Returns dict with lat, lon, city, timezone.
    """
    try:
        resp = requests.get("http://ip-api.com/json/?fields=lat,lon,city,country,timezone", timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "lat": data.get("lat", 20.5937),
                "lon": data.get("lon", 78.9629),
                "city": data.get("city", "India"),
                "country": data.get("country", "India"),
                "timezone": data.get("timezone", "Asia/Kolkata"),
            }
    except Exception:
        pass
    # Default to India center
    return {"lat": 20.5937, "lon": 78.9629, "city": "India", "country": "India", "timezone": "Asia/Kolkata"}
