from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from backend.models import (
    SimulationCreateRequest,
    SimulationMetaResponse,
    SimulationStateResponse,
    SimulationImpactsResponse
)
from backend.services.simulation_service import (
    create_simulation,
    get_simulation_meta,
    calculate_stage_state,
    calculate_simulation_impacts
)

router = APIRouter(prefix="/api/simulation", tags=["Scenario Simulation Engine"])

@router.post("/create", response_model=SimulationMetaResponse)
async def api_create_simulation(req: SimulationCreateRequest):
    """Initializes a new location-specific environmental scenario simulation."""
    try:
        return await create_simulation(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation initialization failed: {str(e)}")

@router.get("/{sim_id}", response_model=SimulationMetaResponse)
def api_get_simulation(sim_id: str):
    """Retrieves simulation metadata and supported scenarios."""
    meta = get_simulation_meta(sim_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Simulation session not found")
    
    return SimulationMetaResponse(
        simulation_id=meta["simulation_id"],
        scenario_type=meta["scenario_type"],
        scenario_title=meta["scenario_title"],
        location_name=meta["location_name"],
        district=meta["district"],
        center=meta["center"],
        supported_scenarios=meta["supported_scenarios"],
        available_hours=meta["available_hours"],
        elevation_amsl=meta["elevation_amsl"],
        distance_to_water_m=meta["distance_to_water_m"],
        nearest_water_name=meta["nearest_water_name"],
        summary_headline=(
            f"Copernicus Elevation: {meta['elevation_amsl']}m AMSL · {meta['district']}. "
            f"Nearest waterbody: {meta['nearest_water_name']} ({meta['distance_to_water_m']}m)."
        )
    )

@router.get("/{sim_id}/state", response_model=SimulationStateResponse)
def api_get_simulation_state(
    sim_id: str,
    hour: int = Query(0, ge=0, le=24, description="Simulation timeline hour (0 to 24)")
):
    """Calculates spatial hazard overlays, affected infrastructure, and metrics for the given hour."""
    meta = get_simulation_meta(sim_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Simulation session not found")
    
    return calculate_stage_state(meta, hour)

@router.get("/{sim_id}/impacts", response_model=SimulationImpactsResponse)
def api_get_simulation_impacts(sim_id: str):
    """Returns milestone comparison across all timeline hours (0, 6, 12, 18, 24)."""
    meta = get_simulation_meta(sim_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Simulation session not found")
    
    return calculate_simulation_impacts(meta)
