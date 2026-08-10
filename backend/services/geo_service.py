"""
services/geo_service.py — Geocoding and proximity utilities.
Uses geopy with Nominatim (OpenStreetMap) — no API key required.
For production scale, swap to Google Maps or Mapbox by changing the geocoder.
"""
import asyncio
import logging
from math import asin, cos, radians, sin, sqrt

from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)

# Single shared geocoder instance (Nominatim requires a meaningful user_agent)
_geocoder = Nominatim(user_agent="disaster-resource-locator/1.0", timeout=10)


# ── Geocoding ──────────────────────────────────────────────────────────────────
async def geocode_location(location_name: str) -> tuple[float, float] | None:
    """
    Convert a location name string to (latitude, longitude).
    Returns None if geocoding fails or location is not found.
    """
    try:
        loop = asyncio.get_running_loop()
        location = await loop.run_in_executor(
            None, 
            lambda: _geocoder.geocode(location_name, exactly_one=True)
        )
        if location:
            return location.latitude, location.longitude
    except (GeocoderTimedOut, GeocoderUnavailable) as exc:
        logger.warning("Geocoding failed for '%s': %s", location_name, exc)
    return None


async def reverse_geocode(latitude: float, longitude: float) -> str | None:
    """
    Convert coordinates to a human-readable address string.
    Returns None on failure.
    """
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: _geocoder.reverse((latitude, longitude), exactly_one=True)
        )
        if result:
            return result.address
    except (GeocoderTimedOut, GeocoderUnavailable) as exc:
        logger.warning("Reverse geocoding failed for (%s, %s): %s", latitude, longitude, exc)
    return None


# ── Haversine Distance ────────────────────────────────────────────────────────
EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance in kilometres between two lat/lon points.
    Uses the Haversine formula.
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def find_nearest_resources(
    incident_lat: float,
    incident_lon: float,
    resources: list[dict],
    max_distance_km: float = 100.0,
) -> list[dict]:
    """
    Given a list of resource dicts (each with 'latitude', 'longitude'),
    return those within max_distance_km sorted by distance ascending.
    Resources missing coordinates are excluded.
    """
    results = []
    for resource in resources:
        lat = resource.get("latitude")
        lon = resource.get("longitude")
        if lat is None or lon is None:
            continue
        dist = haversine_km(incident_lat, incident_lon, lat, lon)
        if dist <= max_distance_km:
            results.append({**resource, "_distance_km": round(dist, 2)})

    results.sort(key=lambda r: r["_distance_km"])
    return results
