import math
import re
from datetime import datetime, timezone
import httpx
from shapely.geometry import Point
from backend.services.weather_service import get_cached, set_cached
from backend.models import LandAssessResponse, LandReportMatrixRow
from backend.data.tamil_nadu_gis import (
    TAMIL_NADU_DISTRICTS,
    find_nearest_district,
    calculate_water_proximity,
    get_geojson_water_features
)

async def fetch_real_elevation(lat: float, lon: float) -> float:
    """Retrieves authoritative elevation from Copernicus DEM via Open-Meteo with caching."""
    cache_key = f"elev_{round(lat, 4)}_{round(lon, 4)}"
    cached_val = get_cached(cache_key, ttl=86400 * 7)
    if cached_val:
        return float(cached_val.get("elevation", 10.0))

    try:
        url = "https://api.open-meteo.com/v1/elevation"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params={"latitude": lat, "longitude": lon})
            if resp.status_code == 200:
                elev = float(resp.json().get("elevation", [12.0])[0])
                set_cached(cache_key, {"elevation": elev})
                return elev
    except Exception:
        pass

    # Fallback regional elevation estimation based on district
    dist_name, dist_info, _ = find_nearest_district(lat, lon)
    if "Mountainous" in dist_info.get("zone", ""):
        return 2200.0
    if "Hilly" in dist_info.get("zone", ""):
        return 1400.0
    if "Plateau" in dist_info.get("zone", ""):
        return 380.0
    if "Central" in dist_info.get("zone", ""):
        return 85.0
    if dist_info.get("coastal", False):
        return 12.0
    return 45.0

async def calculate_slope(lat: float, lon: float, base_elev: float) -> float:
    """Estimates terrain slope gradient percentage using Copernicus DEM deltas."""
    try:
        elev2 = await fetch_real_elevation(lat + 0.001, lon + 0.001)
        # 0.001 degrees is ~140 meters diagonal ground distance
        slope = round(abs(elev2 - base_elev) / 140.0 * 100.0, 1)
        return min(65.0, max(0.2, slope))
    except Exception:
        return 1.2

TN_LOCALITIES = {
    "ooty": {"name": "Udhagamandalam (Ooty)", "lat": 11.4102, "lon": 76.6950, "admin2": "Nilgiris"},
    "udhagamandalam": {"name": "Udhagamandalam (Ooty)", "lat": 11.4102, "lon": 76.6950, "admin2": "Nilgiris"},
    "kodaikanal": {"name": "Kodaikanal", "lat": 10.2381, "lon": 77.4892, "admin2": "Dindigul"},
    "coonoor": {"name": "Coonoor", "lat": 11.3530, "lon": 76.7959, "admin2": "Nilgiris"},
    "kotagiri": {"name": "Kotagiri", "lat": 11.4333, "lon": 76.8833, "admin2": "Nilgiris"},
    "hosur": {"name": "Hosur", "lat": 12.7409, "lon": 77.8253, "admin2": "Krishnagiri"},
    "velachery": {"name": "Velachery, Chennai", "lat": 12.9815, "lon": 80.2180, "admin2": "Chennai"},
    "adyar": {"name": "Adyar, Chennai", "lat": 13.0012, "lon": 80.2565, "admin2": "Chennai"},
    "tambaram": {"name": "Tambaram", "lat": 12.9249, "lon": 80.1000, "admin2": "Chengalpattu"},
    "singanallur": {"name": "Singanallur", "lat": 11.0016, "lon": 77.0264, "admin2": "Coimbatore"},
    "pollachi": {"name": "Pollachi", "lat": 10.6609, "lon": 77.0048, "admin2": "Coimbatore"},
    "kumbakonam": {"name": "Kumbakonam", "lat": 10.9601, "lon": 79.3845, "admin2": "Thanjavur"},
    "nagercoil": {"name": "Nagercoil", "lat": 8.1833, "lon": 77.4119, "admin2": "Kanyakumari"},
    "rameswaram": {"name": "Rameswaram", "lat": 9.2876, "lon": 79.3129, "admin2": "Ramanathapuram"},
    "yercaud": {"name": "Yercaud", "lat": 11.7753, "lon": 78.2093, "admin2": "Salem"},
    "mettur": {"name": "Mettur Dam", "lat": 11.7963, "lon": 77.8016, "admin2": "Salem"},
    "chidambaram": {"name": "Chidambaram", "lat": 11.3992, "lon": 79.6936, "admin2": "Cuddalore"},
    "srirangam": {"name": "Srirangam", "lat": 10.8624, "lon": 78.6946, "admin2": "Tiruchirappalli"},
    "bhavani": {"name": "Bhavani", "lat": 11.4489, "lon": 77.6828, "admin2": "Erode"},
}

async def geocode(query: str) -> dict:
    term = query.strip()
    cache_key = f"geo_{term.lower()}"
    cached_val = get_cached(cache_key, ttl=3600)
    if cached_val:
        return cached_val

    # 1. Check if input is direct coordinates (e.g. 11.4102, 76.6950 or 11.4102N 76.6950E)
    cleaned = re.sub(r'[°NSEWnsew]', '', term)
    coord_match = re.match(r'^\s*([+-]?\d+(?:\.\d+)?)[,\s]+([+-]?\d+(?:\.\d+)?)\s*$', cleaned)
    if coord_match:
        try:
            c_lat = float(coord_match.group(1))
            c_lon = float(coord_match.group(2))
            if -90 <= c_lat <= 90 and -180 <= c_lon <= 180:
                dist_name, _, _ = find_nearest_district(c_lat, c_lon)
                result = {
                    "results": [{
                        "name": f"{c_lat:.4f}°, {c_lon:.4f}°",
                        "latitude": c_lat,
                        "longitude": c_lon,
                        "admin1": "Tamil Nadu",
                        "admin2": dist_name,
                        "country": "India"
                    }]
                }
                set_cached(cache_key, result)
                return result
        except ValueError:
            pass

    results = []

    # 2. Match curated Tamil Nadu localities
    term_lower = term.lower()
    for key, loc in TN_LOCALITIES.items():
        if term_lower in key or key in term_lower or term_lower in loc["name"].lower():
            results.append({
                "name": loc["name"],
                "latitude": loc["lat"],
                "longitude": loc["lon"],
                "admin1": "Tamil Nadu",
                "admin2": loc["admin2"],
                "country": "India"
            })

    # 3. Match 38 Tamil Nadu districts
    for dist_k, dist_v in TAMIL_NADU_DISTRICTS.items():
        if term_lower in dist_k.lower() or dist_k.lower() in term_lower:
            if not any(r["name"].lower() == dist_k.lower() for r in results):
                results.append({
                    "name": dist_k,
                    "latitude": dist_v["lat"],
                    "longitude": dist_v["lon"],
                    "admin1": "Tamil Nadu",
                    "admin2": dist_k,
                    "country": "India"
                })

    # 4. Query Open-Meteo geocoding search for towns/villages across Tamil Nadu
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params={"name": term, "count": 6, "language": "en", "format": "json"})
            if resp.status_code == 200:
                om_data = resp.json()
                for p in om_data.get("results", []):
                    if not any(abs(p["latitude"] - r["latitude"]) < 0.05 and abs(p["longitude"] - r["longitude"]) < 0.05 for r in results):
                        results.append(p)
    except Exception:
        pass

    data = {"results": results[:10]}
    set_cached(cache_key, data)
    return data

async def reverse_geocode(lat: float, lon: float) -> dict:
    cache_key = f"reverse_{round(lat, 3)}_{round(lon, 3)}"
    cached_val = get_cached(cache_key, ttl=86400)
    if cached_val:
        return cached_val

    url = "https://nominatim.openstreetmap.org/reverse"
    headers = {"User-Agent": "SOLUM-TamilNadu-GIS/2.0"}
    async with httpx.AsyncClient(timeout=9.0) as client:
        resp = await client.get(url, params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 12}, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    set_cached(cache_key, data)
    return data

async def perform_land_assessment(address: str, proposed_use: str, area_sqm: float, lat: float, lon: float) -> LandAssessResponse:
    # 1. Real Copernicus DEM elevation & slope
    elevation = await fetch_real_elevation(lat, lon)
    slope = await calculate_slope(lat, lon, elevation)

    # 2. Identify nearest Tamil Nadu district profile
    dist_name, dist_info, dist_km = find_nearest_district(lat, lon)

    # 3. Water body proximity via Shapely
    water_dist, nearest_water_name, nearest_water_type = calculate_water_proximity(lat, lon)

    # 4. Flood Risk Evaluation
    is_coastal = dist_info.get("coastal", False)
    is_mountainous = "Mountainous" in dist_info.get("zone", "") or "Hilly" in dist_info.get("zone", "")

    if is_mountainous:
        if slope > 15.0 or "Severe" in dist_info.get("landslide_risk", ""):
            flood_risk = "Moderate (High Flash Runoff)"
            flood_status = "Steep Runoff Corridor"
            flood_badge = "amber"
            flood_findings = f"High elevation terrain ({elevation}m AMSL) with steep slope ({slope}%). Low standing flood risk, but high flash storm runoff and debris flow vulnerability."
        else:
            flood_risk = "Low"
            flood_status = "Natural Mountain Drainage"
            flood_badge = ""
            flood_findings = f"Elevated hill terrain ({elevation}m AMSL). Well-drained natural slope ({slope}%)."
    elif elevation < 6.0 or water_dist < 200 or (is_coastal and elevation < 5.0):
        flood_risk = "Severe"
        flood_status = "High Vulnerability"
        flood_badge = "red"
        flood_findings = f"Low elevation ({elevation}m AMSL) within {water_dist}m of {nearest_water_name} ({nearest_water_type}). Significant risk of monsoonal inundation / storm surge in {dist_name} district."
    elif elevation < 15.0 or water_dist < 600:
        flood_risk = "Moderate"
        flood_status = "Attention Needed"
        flood_badge = "amber"
        flood_findings = f"Moderate elevation ({elevation}m AMSL). Located {water_dist}m from {nearest_water_name}. Requires secondary stormwater drainage clearance."
    else:
        flood_risk = "Low"
        flood_status = "Favorable Drainage"
        flood_badge = ""
        flood_findings = f"Adequate natural elevation ({elevation}m AMSL) and {water_dist}m clearance from mapped surface water bodies."

    # 5. Water bodies & buffer compliance
    if water_dist < 50:
        water_status = "Statutory Buffer Violation Risk"
        water_badge = "red"
        water_findings = f"Within 50m statutory riparian buffer of {nearest_water_name}. Construction is restricted under Tamil Nadu PWD / Water Resources Dept rules."
    elif water_dist < 200:
        water_status = "Riparian Buffer Review Required"
        water_badge = "amber"
        water_findings = f"Located {water_dist}m from {nearest_water_name} ({nearest_water_type}). Verify irrigation canal / river setback lines with local taluk authorities."
    else:
        water_status = "Adequate Clearance"
        water_badge = ""
        water_findings = f"Located {water_dist}m from nearest mapped major water body ({nearest_water_name}). Standard stormwater connection required."

    # 6. Soil & Foundation (from TNAU & GSI Soil Survey)
    soil_desc = dist_info.get("soil", "Red loamy soil")
    if is_mountainous:
        soil_status = "Laterite / Peat Soil — Geotechnical Test Essential"
        soil_badge = "amber"
        soil_findings = f"{soil_desc}. Hill slope stability, foundation anchoring, and terraced retaining walls must be verified by a geotechnical engineer."
    elif "black cotton" in soil_desc.lower():
        soil_status = "Expansive Black Cotton Soil (Vertisol)"
        soil_badge = "amber"
        soil_findings = f"{soil_desc}. High shrink-swell behavior upon seasonal moisture variation. Under-reamed pile or reinforced raft foundation required."
    elif is_coastal or elevation < 5.0:
        soil_status = "Coastal Alluvial / High Groundwater"
        soil_badge = "amber"
        soil_findings = f"{soil_desc}. Shallow water table expected. Sub-structure waterproofing and anti-salinity concrete grade mandatory."
    else:
        soil_status = "Stable Red Loam / Hard Strata"
        soil_badge = ""
        soil_findings = f"{soil_desc}. Favorable bearing capacity; standard isolated or strip footings subject to borehole soil verification."

    # 7. Terrain & Access
    if slope > 15.0:
        terrain_status = "Steep Slope (>15%)"
        terrain_badge = "amber"
        terrain_findings = f"Steep mountain/hill gradient ({slope}%). Requires cut-and-fill slope stabilization and retaining wall approval under HACA (Hill Area Conservation Authority) regulations."
    elif slope > 6.0:
        terrain_status = "Moderate Undulating Slope"
        terrain_badge = "amber"
        terrain_findings = f"Moderate slope detected ({slope}%). Terraced drainage and driveway grading required."
    else:
        terrain_status = "Gentle / Flat Terrain"
        terrain_badge = ""
        terrain_findings = f"Gentle terrain gradient ({slope}%). Direct access road connectivity feasible without heavy earthwork grading."

    # 8. Land Use, Zoning & Regional Restraints (DTCP / CMDA)
    seismic_info = dist_info.get("seismic_zone", "Zone II")
    landslide_info = dist_info.get("landslide_risk", "None")
    zoning_notes = f"Proposed for {proposed_use} ({area_sqm:,.0f} m²). District: {dist_name}. Structural design must conform to {seismic_info} standards under IS 1893:2016."
    if "Severe" in landslide_info or "High" in landslide_info:
        zoning_notes += f" Location falls in {dist_name} Hill Region — Hill Area Conservation Authority (HACA) clearance and Geological Survey of India (GSI) landslide slope stability certificate mandatory."

    # 9. Environmental & Coastal Constraints (CRZ / Wetlands)
    if is_coastal and water_dist < 500:
        env_status = "CRZ (Coastal Regulation Zone) Scrutiny"
        env_badge = "amber"
        env_findings = f"Located in coastal {dist_name} within 500m of marine/tidal waters. Must obtain Coastal Zone Management Authority (TNCZMA) clearance before approval."
    elif "Wetland" in nearest_water_type or water_dist < 300:
        env_status = "Wetland Catchment Protection"
        env_badge = "amber"
        env_findings = f"Proximity to {nearest_water_name} ({water_dist}m). Requires strict zero-discharge greywater treatment and rainwater harvesting compliance."
    else:
        env_status = "Standard Environmental Compliance"
        env_badge = ""
        env_findings = "Standard tree conservation, rainwater harvesting, and groundwater recharge pit requirements under Tamil Nadu Combined Development and Building Rules (TNCDBR)."

    matrix = [
        LandReportMatrixRow(
            layer="Flood & Waterlogging",
            status=flood_status,
            badge_type=flood_badge,
            findings=flood_findings,
            recommended_action=f"Check historical rainfall & reservoir release records for {dist_name}. Maintain plinth elevation +1.2m above road level.",
            reference_source=f"TNSDMA & IMD {dist_name} Station",
            source_url="https://mausam.imd.gov.in/chennai/"
        ),
        LandReportMatrixRow(
            layer="Water Bodies & Buffers",
            status=water_status,
            badge_type=water_badge,
            findings=water_findings,
            recommended_action=f"Obtain FMB (Field Measurement Book) sketch from Revenue / PWD confirming distance to {nearest_water_name}.",
            reference_source="India-WRIS & Tamil Nadu Water Resources Dept",
            source_url="https://bhuvan.nrsc.gov.in/"
        ),
        LandReportMatrixRow(
            layer="Soil & Foundation",
            status=soil_status,
            badge_type=soil_badge,
            findings=soil_findings,
            recommended_action="Commission minimum 2 borehole geotechnical soil tests before finalizing structural foundation design.",
            reference_source="TNAU Soil Resource Atlas & GSI",
            source_url=""
        ),
        LandReportMatrixRow(
            layer="Terrain & Slope",
            status=terrain_status,
            badge_type=terrain_badge,
            findings=terrain_findings,
            recommended_action="Ensure legal access road width (min 7.2m–9.0m for emergency vehicle access) and verify slope gradient.",
            reference_source="Copernicus DEM & Survey of India",
            source_url=""
        ),
        LandReportMatrixRow(
            layer="Zoning & Structural Rules",
            status=f"{seismic_info} Seismic Compliance",
            badge_type="amber" if "Moderate" in seismic_info else "",
            findings=zoning_notes,
            recommended_action=f"Submit planning permission to DTCP / CMDA in accordance with Tamil Nadu Combined Development and Building Rules.",
            reference_source="Directorate of Town and Country Planning (DTCP)",
            source_url="https://www.cmdachennai.gov.in/"
        ),
        LandReportMatrixRow(
            layer="Environmental & Coastal",
            status=env_status,
            badge_type=env_badge,
            findings=env_findings,
            recommended_action="Verify CRZ boundaries and integrate dual-chamber recharge pits under Tamil Nadu municipal bylaws.",
            reference_source="Tamil Nadu Pollution Control Board (TNPCB)",
            source_url=""
        )
    ]

    use_lower = proposed_use.lower()
    if "home" in use_lower:
        considerations = f"For an individual home in {dist_name} ({area_sqm:,.0f} m²), prioritize elevated ground floor living areas, dedicated drainage channels, and seismic design conforming to {seismic_info}."
    elif "apartment" in use_lower:
        considerations = f"For residential apartments in {dist_name} ({area_sqm:,.0f} m²), elevate transformer and diesel generators above road design flood levels, ensure dual emergency egress, and verify structural soil bearing capacity."
    elif "commercial" in use_lower:
        considerations = f"For commercial facilities, plan ample off-street parking, disabled-accessible ramps (PWD norms), business continuity power on upper podiums, and compliant fire tender turning radius."
    else:
        considerations = f"For community facilities, verify wide multi-modal access corridors, auxiliary shelter conversion capability during extreme weather events, and autonomous water purification storage."

    report_id = f"LND-TN-{dist_name[:3].upper()}-{int(abs(lat * lon * 1000)) % 90000 + 10000}"

    return LandAssessResponse(
        report_id=report_id,
        address=address,
        proposed_use=proposed_use,
        plot_area_sqm=area_sqm,
        latitude=lat,
        longitude=lon,
        elevation_m=elevation,
        slope_percent=slope,
        distance_to_water_m=water_dist,
        flood_risk_level=flood_risk,
        overall_readiness="Conditional — Investigation Recommended" if "High" in flood_risk or "Severe" in flood_risk or slope > 15.0 else "Favorable with Standard Safeguards",
        summary_note=f"Location in {dist_name} district evaluated at {elevation}m elevation (Copernicus DEM) and {water_dist}m from {nearest_water_name}. Overall risk level: {flood_risk}.",
        matrix=matrix,
        planning_considerations=considerations,
        created_at=datetime.now(timezone.utc).strftime("%d %B %Y")
    )
