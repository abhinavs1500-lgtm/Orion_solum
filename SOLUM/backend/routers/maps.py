from fastapi import APIRouter, Query
from typing import Dict, Any
from backend.models import MapsConfigResponse, LocationContextRequest, LocationContextResponse, Marker3D
from backend.services.issues_service import list_issues
from backend.services.geo_service import fetch_real_elevation
from backend.data.tamil_nadu_gis import (
    find_nearest_district,
    calculate_water_proximity,
    get_geojson_water_features
)
from backend.config import settings

router = APIRouter(prefix="/api/maps", tags=["Google Maps 3D Platform"])

@router.get("/config", response_model=MapsConfigResponse)
def get_maps_config():
    return MapsConfigResponse(
        api_key=settings.GOOGLE_MAPS_API_KEY,
        default_center={"lat": 13.0827, "lng": 80.2707, "altitude": 450.0},
        default_tilt=60.0,
        default_heading=20.0,
        default_range=1200.0
    )

@router.get("/overlays")
def get_map_overlays(
    lat: float = Query(13.0827, ge=-90.0, le=90.0),
    lon: float = Query(80.2707, ge=-180.0, le=180.0),
    radius_km: float = Query(40.0, ge=1.0, le=200.0)
) -> Dict[str, Any]:
    """Returns verified GeoJSON layers of rivers, reservoirs, and wetlands around the location."""
    return get_geojson_water_features(lat, lon, radius_km)

@router.post("/location-context", response_model=LocationContextResponse)
async def get_location_context(req: LocationContextRequest):
    elevation = await fetch_real_elevation(req.latitude, req.longitude)
    dist_name, dist_info, _ = find_nearest_district(req.latitude, req.longitude)
    water_dist, nearest_water_name, nearest_water_type = calculate_water_proximity(req.latitude, req.longitude)
    
    flood_zone = f"{dist_name} Drainage Basin ({nearest_water_name} · {water_dist}m)"

    issues = list_issues(status="open")
    markers = []
    for issue in issues:
        lat = issue.latitude or req.latitude
        lon = issue.longitude or req.longitude
        markers.append(Marker3D(
            id=issue.id,
            title=issue.title,
            category=issue.type,
            position={"lat": lat, "lng": lon, "altitude": 15.0},
            status=issue.status,
            priority=issue.priority
        ))

    water_corridors = [
        {
            "name": nearest_water_name,
            "type": nearest_water_type,
            "distance_m": water_dist,
            "district": dist_name
        }
    ]

    return LocationContextResponse(
        latitude=req.latitude,
        longitude=req.longitude,
        elevation_m=elevation,
        flood_zone=flood_zone,
        nearby_issues=markers,
        water_corridors=water_corridors
    )
