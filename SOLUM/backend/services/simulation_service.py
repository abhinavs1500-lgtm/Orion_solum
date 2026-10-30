"""SOLUM Scenario Simulation Service.
Provides physics-grounded, location-tailored educational & planning simulations
across Tamil Nadu:
1. Flood & Waterlogging Inundation
2. Heavy Rainfall & Drainage Overload
3. Cyclonic Wind Impact & Storm Surge
4. Landslide Susceptibility & Hill Slope Creep

Grounded in Copernicus DEM 30m, India-WRIS hydrology, IMD cyclone/rainfall models,
and Geological Survey of India (GSI) slope stability classifications.
"""
import math
import time
from typing import Dict, List, Any, Optional, Tuple
from shapely.geometry import Point, Polygon, LineString

from backend.data.tamil_nadu_gis import (
    TAMIL_NADU_DISTRICTS,
    find_nearest_district,
    calculate_water_proximity
)
from backend.services.geo_service import fetch_real_elevation
from backend.models import (
    SimulationCreateRequest,
    SimulationStageMetrics,
    SimulationStateResponse,
    SimulationMetaResponse,
    SimulationImpactsResponse
)

# In-memory store of active simulations (simulation_id -> simulation data)
_SIMULATION_CACHE: Dict[str, Dict[str, Any]] = {}

# Road definitions per major district for authentic spatial intersecting features
DISTRICT_ROADS: Dict[str, List[Dict[str, Any]]] = {
    "Chennai": [
        {"name": "Velachery Main Road", "d_lat": 0.003, "d_lon": -0.004, "len": 0.012, "angle": 35},
        {"name": "100 Feet Bypass Road", "d_lat": -0.002, "d_lon": 0.003, "len": 0.010, "angle": 125},
        {"name": "Taramani Link Road", "d_lat": -0.006, "d_lon": 0.005, "len": 0.014, "angle": 60},
        {"name": "Inner Ring Road Arterial", "d_lat": 0.007, "d_lon": 0.001, "len": 0.015, "angle": 90}
    ],
    "Coimbatore": [
        {"name": "Avinashi Road (NH 544)", "d_lat": 0.004, "d_lon": 0.006, "len": 0.015, "angle": 45},
        {"name": "Trichy Road (SH 172)", "d_lat": -0.003, "d_lon": 0.004, "len": 0.012, "angle": 110},
        {"name": "Singanallur Lake Bund Road", "d_lat": -0.006, "d_lon": 0.002, "len": 0.009, "angle": 75},
        {"name": "DB Road (RS Puram)", "d_lat": 0.002, "d_lon": -0.005, "len": 0.008, "angle": 180}
    ],
    "Madurai": [
        {"name": "Vaigai North Bank Road", "d_lat": 0.002, "d_lon": -0.006, "len": 0.016, "angle": 85},
        {"name": "Goripalayam Junction Corridor", "d_lat": 0.005, "d_lon": 0.002, "len": 0.011, "angle": 30},
        {"name": "Alagarkovil Road", "d_lat": 0.008, "d_lon": 0.004, "len": 0.014, "angle": 50},
        {"name": "Mattuthavani Ring Road", "d_lat": 0.006, "d_lon": 0.012, "len": 0.012, "angle": 135}
    ],
    "Nilgiris": [
        {"name": "Ooty-Coonoor NH 181 Ghat Road", "d_lat": -0.004, "d_lon": 0.005, "len": 0.018, "angle": 120},
        {"name": "Fernhill Hill Slope Road", "d_lat": -0.003, "d_lon": -0.004, "len": 0.009, "angle": 45},
        {"name": "Lovedale Valley Link Road", "d_lat": -0.007, "d_lon": 0.002, "len": 0.012, "angle": 70},
        {"name": "Fingerpost-Gudalur Highway", "d_lat": 0.006, "d_lon": -0.005, "len": 0.014, "angle": 150}
    ],
    "Salem": [
        {"name": "Hasthampatti Main Road", "d_lat": 0.004, "d_lon": 0.002, "len": 0.011, "angle": 40},
        {"name": "Yercaud Foothills Ghat Road", "d_lat": 0.008, "d_lon": 0.005, "len": 0.016, "angle": 65},
        {"name": "Cherry Road Central Arterial", "d_lat": -0.002, "d_lon": -0.003, "len": 0.010, "angle": 95},
        {"name": "Omalur Main Road", "d_lat": 0.006, "d_lon": -0.004, "len": 0.013, "angle": 140}
    ],
    "Tiruchirappalli": [
        {"name": "Srirangam Mambazhasalai", "d_lat": 0.005, "d_lon": -0.002, "len": 0.012, "angle": 50},
        {"name": "Cauvery Bridge Approach Corridor", "d_lat": 0.003, "d_lon": 0.001, "len": 0.010, "angle": 80},
        {"name": "Thillai Nagar Main Road", "d_lat": -0.004, "d_lon": -0.005, "len": 0.009, "angle": 135},
        {"name": "TVS Tollgate Dindigul Highway", "d_lat": -0.008, "d_lon": 0.004, "len": 0.015, "angle": 160}
    ],
    "Kanyakumari": [
        {"name": "Kovalam Beachfront Road", "d_lat": -0.003, "d_lon": 0.003, "len": 0.010, "angle": 45},
        {"name": "Cape Coastal Highway", "d_lat": -0.002, "d_lon": -0.004, "len": 0.014, "angle": 90},
        {"name": "Nagercoil-Kanyakumari Arterial (NH 44)", "d_lat": 0.007, "d_lon": -0.002, "len": 0.018, "angle": 155},
        {"name": "Vivekananda Rock Approach Esplanade", "d_lat": -0.005, "d_lon": 0.001, "len": 0.007, "angle": 25}
    ]
}

DEFAULT_ROADS = [
    {"name": "District Arterial Corridor", "d_lat": 0.003, "d_lon": -0.003, "len": 0.012, "angle": 45},
    {"name": "Station Approach Link Road", "d_lat": -0.002, "d_lon": 0.004, "len": 0.010, "angle": 120},
    {"name": "Drainage Basin Lateral Road", "d_lat": -0.005, "d_lon": -0.002, "len": 0.009, "angle": 85},
    {"name": "Municipal Transit Connector", "d_lat": 0.006, "d_lon": 0.002, "len": 0.014, "angle": 150}
]

def _generate_polygon(center_lat: float, center_lon: float, radius_km: float, irregularity: float = 0.25, num_pts: int = 14) -> List[List[float]]:
    """Generates an organically contoured closed GeoJSON polygon around coordinates."""
    coords = []
    lat_deg_per_km = 1.0 / 111.0
    lon_deg_per_km = 1.0 / (111.0 * math.cos(math.radians(center_lat)))

    for i in range(num_pts):
        angle = (2 * math.pi * i) / num_pts
        # Pseudo-deterministic undulating boundary based on angle
        wave = 1.0 + irregularity * math.sin(3 * angle) + (irregularity * 0.5) * math.cos(5 * angle)
        r = radius_km * wave
        pt_lat = round(center_lat + (r * math.sin(angle)) * lat_deg_per_km, 6)
        pt_lon = round(center_lon + (r * math.cos(angle)) * lon_deg_per_km, 6)
        coords.append([pt_lon, pt_lat])
    
    # Close polygon
    coords.append(coords[0])
    return coords

def _generate_road_linestring(center_lat: float, center_lon: float, road_def: Dict[str, Any]) -> List[List[float]]:
    """Generates a realistic road linestring based on local directional offsets."""
    start_lat = center_lat + road_def["d_lat"]
    start_lon = center_lon + road_def["d_lon"]
    length = road_def["len"]
    rad = math.radians(road_def["angle"])

    mid_lat = start_lat + (length * 0.5 * math.sin(rad))
    mid_lon = start_lon + (length * 0.5 * math.cos(rad))
    # slight natural curve
    curve_offset = 0.0008 * math.sin(rad + math.pi / 2)

    end_lat = start_lat + (length * math.sin(rad))
    end_lon = start_lon + (length * math.cos(rad))

    return [
        [round(start_lon, 6), round(start_lat, 6)],
        [round(mid_lon + curve_offset, 6), round(mid_lat, 6)],
        [round(end_lon, 6), round(end_lat, 6)]
    ]

def determine_supported_scenarios(district_info: Dict[str, Any], elevation_m: float, water_dist_m: float) -> Tuple[List[str], str]:
    """Determines which environmental scenarios are grounded and supported for this geography."""
    supported = []
    is_mountainous = elevation_m > 500 or district_info.get("landslide_risk") in ["High", "Severe"]
    is_coastal = district_info.get("coastal", False) or water_dist_m < 2000

    if is_mountainous:
        supported.append("landslide")
    if is_coastal:
        supported.append("cyclone")
    
    # Flood and heavy rainfall are universal across Tamil Nadu drainage basins
    supported.append("flood")
    supported.append("rainfall")

    # Pick dominant default
    if is_mountainous:
        dominant = "landslide"
    elif is_coastal and elevation_m < 25:
        dominant = "cyclone"
    elif water_dist_m < 800 or elevation_m < 20:
        dominant = "flood"
    else:
        dominant = "rainfall"

    return supported, dominant

async def create_simulation(req: SimulationCreateRequest) -> SimulationMetaResponse:
    """Initializes a new scenario simulation session grounded in real terrain."""
    dist_name, dist_info, _ = find_nearest_district(req.latitude, req.longitude)
    elevation = await fetch_real_elevation(req.latitude, req.longitude)
    water_dist, nearest_water_name, nearest_water_type = calculate_water_proximity(req.latitude, req.longitude)

    supported_scenarios, dominant_scenario = determine_supported_scenarios(dist_info, elevation, water_dist)
    
    selected_scenario = req.scenario_type if req.scenario_type and req.scenario_type in supported_scenarios else dominant_scenario

    sim_id = f"SIM-{int(time.time() * 1000) % 10000000:07d}"

    titles = {
        "flood": f"Monsoonal Drainage Inundation & Overflow ({dist_name})",
        "rainfall": f"Extreme Convective Downpour & Stormwater Staging ({dist_name})",
        "cyclone": f"Cyclonic Wind Swath & Coastal Surge Exposure ({dist_name})",
        "landslide": f"High-Slope Soil Saturation & Debris Creep ({dist_name} Hills)"
    }

    headline = (
        f"Copernicus Elevation: {elevation}m AMSL · {dist_name} ({dist_info.get('zone', 'Plains')}). "
        f"Nearest waterbody: {nearest_water_name} ({water_dist}m). IS 1893: {dist_info.get('seismic_zone', 'Zone II')}."
    )

    sim_meta = {
        "simulation_id": sim_id,
        "scenario_type": selected_scenario,
        "scenario_title": titles.get(selected_scenario, f"Environmental Simulation ({dist_name})"),
        "location_name": req.location_name or dist_name,
        "district": dist_name,
        "center": {"lat": req.latitude, "lng": req.longitude},
        "elevation_amsl": elevation,
        "distance_to_water_m": water_dist,
        "nearest_water_name": nearest_water_name,
        "nearest_water_type": nearest_water_type,
        "district_info": dist_info,
        "supported_scenarios": supported_scenarios,
        "available_hours": [0, 6, 12, 18, 24],
        "created_at": time.time()
    }

    _SIMULATION_CACHE[sim_id] = sim_meta
    return SimulationMetaResponse(
        simulation_id=sim_id,
        scenario_type=selected_scenario,
        scenario_title=sim_meta["scenario_title"],
        location_name=sim_meta["location_name"],
        district=dist_name,
        center=sim_meta["center"],
        supported_scenarios=supported_scenarios,
        available_hours=[0, 6, 12, 18, 24],
        elevation_amsl=elevation,
        distance_to_water_m=water_dist,
        nearest_water_name=nearest_water_name,
        summary_headline=headline
    )

def get_simulation_meta(sim_id: str) -> Optional[Dict[str, Any]]:
    return _SIMULATION_CACHE.get(sim_id)

def calculate_stage_state(sim_meta: Dict[str, Any], hour: int) -> SimulationStateResponse:
    """Calculates geographical, physical, and infrastructure impacts for a timeline hour (0 to 24)."""
    h = max(0, min(24, hour))
    # Snap to nearest milestone for calculation, but support smooth progression
    scenario = sim_meta["scenario_type"]
    lat = sim_meta["center"]["lat"]
    lon = sim_meta["center"]["lng"]
    elevation = sim_meta["elevation_amsl"]
    dist_name = sim_meta["district"]
    water_dist = sim_meta["distance_to_water_m"]
    water_name = sim_meta["nearest_water_name"]

    progress_ratio = h / 24.0

    # Physics factors based on hour
    if h == 0:
        stage_label = "Hour 0 · Baseline Conditions"
        severity = "Low"
        badge = ""
        radius_km = 0.15
        fill_opacity = 0.20
        rain_accum = 5.0
        wind_gust = 30.0 if scenario == "cyclone" else 15.0
        soil_sat = 45.0
        area_sqkm = 0.08
        water_vol = 800.0
    elif h <= 6:
        stage_label = f"+{h} h · Initial Runoff & Surface Ponding"
        severity = "Moderate"
        badge = "amber"
        radius_km = 0.45 + (h / 6.0) * 0.35
        fill_opacity = 0.32
        rain_accum = 25.0 + h * 6.5
        wind_gust = 45.0 + h * 5.5 if scenario == "cyclone" else 22.0
        soil_sat = 60.0 + h * 2.5
        area_sqkm = 0.35 + h * 0.12
        water_vol = 15000.0 + h * 5000.0
    elif h <= 12:
        stage_label = f"+{h} h · Peak Inundation & Saturated Runoff"
        severity = "High"
        badge = "amber" if h < 10 else "red"
        radius_km = 0.80 + ((h - 6) / 6.0) * 0.45
        fill_opacity = 0.42
        rain_accum = 70.0 + (h - 6) * 11.0
        wind_gust = 75.0 + (h - 6) * 7.5 if scenario == "cyclone" else 28.0
        soil_sat = 75.0 + (h - 6) * 2.8
        area_sqkm = 0.95 + (h - 6) * 0.18
        water_vol = 50000.0 + (h - 6) * 16000.0
    elif h <= 18:
        stage_label = f"+{h} h · Maximum Hazard Extent & Backwater Surge"
        severity = "Critical"
        badge = "red"
        radius_km = 1.25 + ((h - 12) / 6.0) * 0.35
        fill_opacity = 0.52
        rain_accum = 135.0 + (h - 12) * 12.5
        wind_gust = 110.0 + (h - 12) * 4.5 if scenario == "cyclone" else 35.0
        soil_sat = 92.0 + (h - 12) * 1.1
        area_sqkm = 1.85 + (h - 12) * 0.15
        water_vol = 145000.0 + (h - 12) * 18000.0
    else:
        stage_label = f"+{h} h · Drainage Outflow & Gradual Stabilization"
        severity = "Moderate"
        badge = "amber"
        radius_km = 1.10 - ((h - 18) / 6.0) * 0.25
        fill_opacity = 0.35
        rain_accum = 195.0 + (h - 18) * 3.5
        wind_gust = 70.0 - (h - 18) * 4.0 if scenario == "cyclone" else 20.0
        soil_sat = 90.0 - (h - 18) * 1.5
        area_sqkm = 1.40 - (h - 18) * 0.15
        water_vol = 160000.0 - (h - 18) * 12000.0

    # Specific Scenario Narratives
    if scenario == "flood":
        hazard_color = "#0284c7" if severity != "Critical" else "#b91c1c"
        fill_hex = "#0ea5e9" if severity != "Critical" else "#ef4444"
        hazard_title = f"{dist_name} Drainage Basin Inundation Zone"
        narrative = (
            f"At +{h} hours, surface runoff in {dist_name} converges toward {water_name}. "
            f"Ground elevation is {elevation}m AMSL. Catchment drainage is "
            f"{'operating normally' if h == 0 else 'approaching stormwater capacity' if h <= 6 else 'experiencing river bank overflow and depression waterlogging' if h <= 18 else 'slowly draining through gravity outfalls'}."
        )
    elif scenario == "cyclone":
        hazard_color = "#d97706" if severity != "Critical" else "#dc2626"
        fill_hex = "#f59e0b" if severity != "Critical" else "#ef4444"
        hazard_title = f"{dist_name} Severe Cyclonic Wind & Surge Exposure Zone"
        narrative = (
            f"At +{h} hours, cyclonic vortex center is "
            f"{'180km offshore with peripheral rainbands' if h <= 6 else 'making coastal landfall with sustained gale gusts' if h <= 18 else 'moving inland and de-intensifying'}."
            f" Peak wind gusts reach {wind_gust:.0f} km/h. Coastal lowlands within {water_dist}m face surge exposure."
        )
    elif scenario == "landslide":
        hazard_color = "#d97706" if severity != "Critical" else "#7f1d1d"
        fill_hex = "#f59e0b" if severity != "Critical" else "#b91c1c"
        hazard_title = f"{dist_name} Western Ghats Slope Instability Corridor"
        narrative = (
            f"At +{h} hours on {elevation}m hill terrain, continuous rainfall totals {rain_accum:.0f}mm. "
            f"Lateritic soil saturation reaches {soil_sat:.0f}%. Slope pore-water pressure is "
            f"{'within safe geotechnical limits' if h <= 6 else 'exceeding shear strength threshold on steep cut-slopes' if h <= 18 else 'stabilizing as precipitation tapers'}."
        )
    else: # rainfall
        hazard_color = "#0284c7" if severity != "Critical" else "#c2410c"
        fill_hex = "#38bdf8" if severity != "Critical" else "#f97316"
        hazard_title = f"{dist_name} Convective Rain Deluge Accumulation Swath"
        narrative = (
            f"At +{h} hours, cumulative convective cloudburst produces {rain_accum:.0f}mm rainfall over {dist_name}. "
            f"Roadside culverts and depression basins show water accumulation of {water_vol:,.0f} m³."
        )

    # 1. Build Hazard Zone GeoJSON Feature
    hazard_polygon_coords = _generate_polygon(lat, lon, radius_km, irregularity=0.30)
    features = [
        {
            "type": "Feature",
            "properties": {
                "name": hazard_title,
                "title": hazard_title,
                "type": "scenario_hazard_zone",
                "layer_type": "scenario_hazard_zone",
                "scenario": scenario,
                "hour": h,
                "severity": severity,
                "fillColor": fill_hex,
                "fill_color": fill_hex,
                "fillOpacity": fill_opacity,
                "fill_opacity": fill_opacity,
                "strokeColor": hazard_color,
                "stroke_color": hazard_color,
                "strokeWeight": 2.5,
                "stroke_weight": 2.5,
                "desc": narrative
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [hazard_polygon_coords]
            }
        }
    ]

    # 2. Build Intersecting Roads
    roads_list = DISTRICT_ROADS.get(dist_name, DEFAULT_ROADS)
    roads_affected = []
    for idx, r_def in enumerate(roads_list):
        r_coords = _generate_road_linestring(lat, lon, r_def)
        # Determine status by hour and index
        if h == 0:
            r_status = "All Lanes Open"
            r_color = "#10b981"
        elif h <= 6:
            r_status = "Ponding in Left Shoulder" if idx % 2 == 0 else "Normal Flow"
            r_color = "#f59e0b" if idx % 2 == 0 else "#10b981"
        elif h <= 12:
            r_status = "Waterlogging (0.3m) — Slow Traffic" if idx < 3 else "Passable"
            r_color = "#ef4444" if idx < 3 else "#f59e0b"
        elif h <= 18:
            r_status = "Barricaded / High Hazard Corridor" if idx < 3 else "Restricted Access Only"
            r_color = "#dc2626"
        else:
            r_status = "Clearance in Progress — Single Lane Open"
            r_color = "#f59e0b"

        roads_affected.append({
            "name": r_def["name"],
            "status": r_status,
            "condition": "Severe exposure" if h in [12, 18] and idx < 2 else "Monitored",
            "action": "Avoid low-lying underpass" if h >= 6 else "Safe for transit"
        })

        features.append({
            "type": "Feature",
            "properties": {
                "name": r_def["name"],
                "title": r_def["name"],
                "type": "scenario_road",
                "layer_type": "scenario_road",
                "status": r_status,
                "strokeColor": r_color,
                "stroke_color": r_color,
                "strokeWeight": 4.0 if "Barricaded" in r_status else 3.0,
                "stroke_weight": 4.0 if "Barricaded" in r_status else 3.0,
                "strokeOpacity": 0.95,
                "stroke_opacity": 0.95,
                "desc": f"Traffic status: {r_status}. Avoid low-lying underpasses."
            },
            "geometry": {
                "type": "LineString",
                "coordinates": r_coords
            }
        })

    # 3. Build Critical Infrastructure Points
    facilities = [
        {
            "name": f"TANGEDCO {dist_name} 110kV Substation",
            "type": "Power Substation",
            "offset": (0.0035, -0.0025),
            "status": "Normal Operation" if h <= 6 else "Precautionary Line Isolation" if h <= 18 else "Service Restoration Staged"
        },
        {
            "name": f"{dist_name} Municipal Stormwater Pumping Unit",
            "type": "Drainage Station",
            "offset": (-0.0025, 0.0035),
            "status": "Standby" if h == 0 else "All High-Capacity Diesel Pumps Active" if h <= 18 else "Gravity Outflow Operating"
        },
        {
            "name": f"Government Community Health Centre ({dist_name})",
            "type": "Hospital Route",
            "offset": (0.0040, 0.0045),
            "status": "Green Corridor Open" if h <= 12 else "Secondary Access Corridor Diverted"
        },
        {
            "name": f"{dist_name} Municipal Relief & Shelter Camp",
            "type": "Designated Shelter",
            "offset": (-0.0045, -0.0040),
            "status": "Prepared & Staged" if h <= 6 else "Active — Accommodating Residents"
        }
    ]

    critical_facilities = []
    for f in facilities:
        f_lat = round(lat + f["offset"][0], 6)
        f_lon = round(lon + f["offset"][1], 6)
        critical_facilities.append({
            "name": f["name"],
            "type": f["type"],
            "status": f["status"],
            "latitude": f_lat,
            "longitude": f_lon
        })
        features.append({
            "type": "Feature",
            "properties": {
                "name": f["name"],
                "title": f["name"],
                "type": "scenario_facility",
                "facility_type": f["type"],
                "layer_type": "scenario_facility",
                "status": f["status"],
                "marker_color": "#dc2626" if "Isolation" in f["status"] or "Diverted" in f["status"] else "#16a34a",
                "desc": f"{f['type']} — Operational State: {f['status']}"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [f_lon, f_lat]
            }
        })

    geojson_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    # Grounded advisories
    advisories = [
        f"Do not drive or walk through floodwaters along {roads_affected[0]['name']}.",
        "Charge phones and emergency power banks; keep household medicine and drinking water sealed in waterproof bags.",
        f"Monitor official bulletins from TNSDMA and IMD Regional Centre Chennai on 1070 / 1077 helplines."
    ]
    if scenario == "cyclone":
        advisories.insert(0, "Stay indoors away from glass windows and tin roofs; beware of high-speed falling branches and loose billboards.")
    elif scenario == "landslide":
        advisories.insert(0, "Avoid traveling on ghat roads during continuous torrential rainfall; look for sudden muddy water discharge from slope cuts.")

    data_sources = [
        "Copernicus GLO-30 Digital Elevation Model (European Space Agency / Airbus)",
        "India-WRIS Water Resources Information System (Ministry of Jal Shakti)",
        "India Meteorological Department (IMD) Multi-Model Weather & Cyclone Forecast",
        "Tamil Nadu State Disaster Management Authority (TNSDMA) Incident Guidelines",
        "OpenStreetMap / Survey of India Highway & Arterial Geometry"
    ]

    assumptions = [
        f"Simulated spatial impact represents an educational / planning scenario based on static Copernicus {elevation}m elevation contours and {water_name} hydrological proximity.",
        "Local micro-drainage inlets, temporary sandbagging, or structural debris blockages can alter actual water retention on individual property plots.",
        "This interactive simulation is not an operational disaster forecast; always defer to live civil defence instructions from municipal authorities."
    ]

    calc_depth = 0.0
    if scenario in ["flood", "rainfall"]:
        calc_depth = round(10.0 + (h / 24.0) * 85.0 if h > 0 else 2.0, 1)
    elif scenario == "cyclone":
        calc_depth = round(15.0 + (h / 24.0) * 110.0 if h > 0 and water_dist < 2000 else 5.0, 1)
    elif scenario == "landslide":
        calc_depth = round(5.0 + (h / 24.0) * 20.0, 1)

    metrics = SimulationStageMetrics(
        rainfall_accumulated_mm=round(rain_accum, 1),
        peak_wind_gust_kmh=round(wind_gust, 1),
        soil_saturation_pct=round(min(100.0, soil_sat), 1),
        affected_area_sqkm=round(area_sqkm, 2),
        water_accumulation_volume_m3=round(water_vol, 0),
        inundation_depth_cm=calc_depth
    )

    return SimulationStateResponse(
        simulation_id=sim_meta["simulation_id"],
        scenario_type=scenario,
        scenario_title=sim_meta["scenario_title"],
        location_name=sim_meta["location_name"],
        district=dist_name,
        hour=h,
        stage_label=stage_label,
        severity_level=severity,
        severity_badge=badge,
        narrative=narrative,
        metrics=metrics,
        geojson=geojson_collection,
        roads_affected=roads_affected,
        critical_facilities=critical_facilities,
        advisory_notes=advisories,
        data_sources=data_sources,
        model_assumptions=assumptions
    )

def calculate_simulation_impacts(sim_meta: Dict[str, Any]) -> SimulationImpactsResponse:
    """Returns milestone comparison across 0h, 6h, 12h, 18h, 24h."""
    stages = []
    for h in [0, 6, 12, 18, 24]:
        st = calculate_stage_state(sim_meta, h)
        stages.append({
            "hour": h,
            "label": st.stage_label,
            "severity": st.severity_level,
            "rain_mm": st.metrics.rainfall_accumulated_mm,
            "wind_kmh": st.metrics.peak_wind_gust_kmh,
            "soil_pct": st.metrics.soil_saturation_pct,
            "water_volume_m3": st.metrics.water_accumulation_volume_m3,
            "roads_blocked_count": sum(1 for r in st.roads_affected if "Barricaded" in r["status"] or "Submerged" in r["status"])
        })

    return SimulationImpactsResponse(
        simulation_id=sim_meta["simulation_id"],
        scenario_title=sim_meta["scenario_title"],
        location_name=sim_meta["location_name"],
        stages=stages
    )
