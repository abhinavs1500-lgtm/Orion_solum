from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Any, Dict
from datetime import datetime

# --- Issues & Complaints ---
class IssueBase(BaseModel):
    title: str = Field(..., max_length=150)
    place: str = Field(..., max_length=160)
    district: Optional[str] = "Chennai"
    city: Optional[str] = "Chennai"
    locality: Optional[str] = "Velachery"
    type: str = Field(..., max_length=50) # 'Electricity', 'Drainage', 'Roads', 'Telecom', 'Other'
    priority: str = Field(default="Unassessed") # 'Critical', 'High', 'Medium', 'Unassessed'
    status: str = Field(default="Assessment") # 'Assessment', 'Assigned', 'In progress', 'Resolved'
    progress: int = Field(default=0, ge=0, le=100)
    crew: int = Field(default=0, ge=0)
    cost: int = Field(default=0, ge=0)
    hours: int = Field(default=0, ge=0)
    owner: str = Field(default="Awaiting assignment", max_length=120)
    reason: Optional[str] = ""
    dependency: Optional[str] = "Not assessed"
    latest_update: str = Field(..., min_length=5, max_length=1000)
    risk_advisory: Optional[str] = "Exercise caution around active work areas."
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    data_source: Optional[str] = "Demonstration baseline (SOLUM)"
    record_type: Optional[str] = "demonstration" # 'demonstration', 'user-submitted', 'real'

class IssueCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    category: str = Field(..., max_length=50)
    place: str = Field(..., min_length=2, max_length=160)
    description: str = Field(..., min_length=10, max_length=1000)
    district: Optional[str] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class IssueResponse(BaseModel):
    id: str
    title: str
    place: str
    district: Optional[str] = "Chennai"
    city: Optional[str] = "Chennai"
    locality: Optional[str] = "Velachery"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    type: str
    icon: str
    priority: str
    status: str
    progress: int
    crew: int
    cost: int
    hours: int
    owner: str
    reason: str
    dependency: str
    update: str # mapped from latest_update for direct frontend compatibility
    steps: List[str]
    risk: str
    evidence: List[str] = []
    data_source: str = "Demonstration baseline (SOLUM)"
    record_type: str = "demonstration" # 'demonstration', 'user-submitted', 'real'
    local: bool = False
    created_at: str
    updated_at: str

# Complaint alias models for complete API consistency
ComplaintResponse = IssueResponse

class IssueStatsResponse(BaseModel):
    total: int
    in_progress: int
    resolved: int
    awaiting: int
    district: Optional[str] = None
    locality: Optional[str] = None

ComplaintStatsResponse = IssueStatsResponse

# --- Officials ---
class OfficialUpdateCreate(BaseModel):
    issue_id: str
    status: str # 'Assessment', 'Assigned', 'In progress', 'Resolved'
    progress: int = Field(..., ge=0, le=100)
    crew: int = Field(..., ge=0)
    cost: int = Field(..., ge=0)
    hours: int = Field(..., ge=0)
    owner: str = Field(..., min_length=2, max_length=120)
    note: str = Field(..., min_length=5, max_length=1000)
    actor_role: Optional[str] = "District coordination officer"

    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v, info):
        return v

class AuditLogResponse(BaseModel):
    id: int
    issue_id: str
    status: str
    note: str
    actor_role: Optional[str]
    crew_allocated: Optional[int]
    cost_allocated: Optional[int]
    created_at: str

class OfficialLoginRequest(BaseModel):
    official_id: str = Field(..., min_length=2, max_length=50)
    passcode: str = Field(..., min_length=4, max_length=50)
    role: Optional[str] = "District coordination officer"
    district: Optional[str] = "Chennai"

class OfficialAuthResponse(BaseModel):
    token: str
    official_id: str
    name: str
    role: str
    district: str
    expires_at: str

class OfficialStatsResponse(BaseModel):
    total_reported: int
    pending_issues: int
    in_progress: int
    resolved: int
    critical_priority: int
    assigned_teams: int
    repair_progress_avg: int
    total_cost: int
    total_crew: int
    district: str
    locality: Optional[str] = None

# --- Land Assessment ---
class LandAssessRequest(BaseModel):
    address: str = Field(..., min_length=3, max_length=200)
    proposed_use: str = Field(default="Individual home") # 'Individual home', 'Apartment building', 'Commercial building', 'Community facility'
    plot_area_sqm: float = Field(..., gt=0, le=10_000_000)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

class LandReportMatrixRow(BaseModel):
    layer: str
    status: str # e.g. 'Clear', 'Attention needed', 'Survey required', 'High exposure'
    badge_type: str # 'amber', 'red', ''
    findings: str
    recommended_action: str
    reference_source: str
    source_url: str

class LandAssessResponse(BaseModel):
    report_id: str
    address: str
    proposed_use: str
    plot_area_sqm: float
    latitude: float
    longitude: float
    elevation_m: float
    slope_percent: float
    distance_to_water_m: float
    flood_risk_level: str
    overall_readiness: str
    summary_note: str
    matrix: List[LandReportMatrixRow]
    planning_considerations: str
    created_at: str

# --- AI Chat ---
class ChatLocation(BaseModel):
    name: Optional[str] = "Chennai"
    district: Optional[str] = "Chennai"
    city: Optional[str] = "Chennai"
    lat: Optional[float] = 13.0827
    lon: Optional[float] = 80.2707

class ChatMessage(BaseModel):
    role: str = "user" # 'user', 'assistant', 'system'
    content: str

class ChatContext(BaseModel):
    page: Optional[str] = None
    current_page: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    assessment: Optional[Dict[str, Any]] = None
    last_assessment: Optional[Dict[str, Any]] = None
    active_complaint: Optional[Dict[str, Any]] = None
    simulation: Optional[Dict[str, Any]] = None
    map_mode: Optional[str] = None

class ChatAction(BaseModel):
    label: str
    action_type: str # 'navigate', 'location', 'filter', 'assessment'
    target: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    location: Optional[ChatLocation] = None
    history: Optional[List[ChatMessage]] = []
    context: Optional[ChatContext] = None

class ChatResponse(BaseModel):
    reply: str
    actions: Optional[List[ChatAction]] = []
    source_title: str = "IMD Chennai & NDMA Guidelines"
    source_url: str = "https://mausam.imd.gov.in/chennai/mcdata/dos%26donts.pdf"
    suggested_questions: Optional[List[str]] = []

# --- Maps 3D ---
class MapsConfigResponse(BaseModel):
    api_key: str
    default_center: Dict[str, float]
    default_tilt: float = 60.0
    default_heading: float = 20.0
    default_range: float = 1200.0

class LocationContextRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

class Marker3D(BaseModel):
    id: str
    title: str
    category: str
    position: Dict[str, float] # {lat, lng, altitude}
    status: str
    priority: str

class LocationContextResponse(BaseModel):
    latitude: float
    longitude: float
    elevation_m: float
    flood_zone: str
    nearby_issues: List[Marker3D]
    water_corridors: List[Dict[str, Any]]

# --- Scenario Simulation Engine ---
class SimulationCreateRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    scenario_type: Optional[str] = Field(default="auto") # 'auto', 'flood', 'rainfall', 'cyclone', 'landslide'
    location_name: Optional[str] = "Selected Area"
    city: Optional[str] = None
    district: Optional[str] = None
    duration_hours: Optional[int] = 24

    @model_validator(mode="before")
    @classmethod
    def reconcile_coordinates(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if values.get("latitude") is None and values.get("lat") is not None:
                values["latitude"] = values["lat"]
            if values.get("longitude") is None and values.get("lon") is not None:
                values["longitude"] = values["lon"]
            if values.get("location_name") is None and values.get("city") is not None:
                values["location_name"] = values["city"]
        return values

class SimulationStageMetrics(BaseModel):
    rainfall_accumulated_mm: float
    peak_wind_gust_kmh: float
    soil_saturation_pct: float
    affected_area_sqkm: float
    water_accumulation_volume_m3: float
    inundation_depth_cm: Optional[float] = 0.0

class SimulationStateResponse(BaseModel):
    simulation_id: str
    scenario_type: str
    scenario_title: str
    location_name: str
    district: str
    hour: int
    stage_label: str
    severity_level: str  # 'Low', 'Moderate', 'Severe', 'Critical'
    severity_badge: str  # '', 'amber', 'red'
    narrative: str
    metrics: SimulationStageMetrics
    geojson: Dict[str, Any]
    roads_affected: List[Dict[str, Any]]
    critical_facilities: List[Dict[str, Any]]
    advisory_notes: List[str]
    data_sources: List[str]
    model_assumptions: List[str]

class SimulationMetaResponse(BaseModel):
    simulation_id: str
    scenario_type: str
    scenario_title: str
    location_name: str
    district: str
    center: Dict[str, float]
    supported_scenarios: List[str]
    available_hours: List[int]
    elevation_amsl: float
    distance_to_water_m: float
    nearest_water_name: str
    summary_headline: str

class SimulationImpactsResponse(BaseModel):
    simulation_id: str
    scenario_title: str
    location_name: str
    stages: List[Dict[str, Any]]
