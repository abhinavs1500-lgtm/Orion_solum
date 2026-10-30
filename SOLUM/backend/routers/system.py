from fastapi import APIRouter, HTTPException, Query
from backend.services.weather_service import get_weather
from backend.services.geo_service import geocode, reverse_geocode
from backend.services.news_service import get_news
from backend.config import settings

router = APIRouter(prefix="/api", tags=["System & Environmental"])

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "maps_3d_configured": bool(settings.GOOGLE_MAPS_API_KEY)
    }

@router.get("/weather")
async def weather_endpoint(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0)
):
    try:
        return await get_weather(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Weather service unavailable: {str(e)}")

@router.get("/geocode")
async def geocode_endpoint(q: str = Query(..., min_length=2, max_length=100)):
    try:
        return await geocode(q)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Geocoding service unavailable: {str(e)}")

@router.get("/reverse")
async def reverse_endpoint(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0)
):
    try:
        return await reverse_geocode(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Reverse geocoding unavailable: {str(e)}")

@router.get("/news")
async def news_endpoint(
    region: str = Query("Chennai", min_length=2, max_length=100),
    scope: str = Query("district", pattern="^(district|state|national)$")
):
    try:
        return await get_news(region, scope)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Disaster news service unavailable: {str(e)}")
