from fastapi import APIRouter, HTTPException
from backend.models import LandAssessRequest, LandAssessResponse
from backend.services.geo_service import perform_land_assessment

router = APIRouter(prefix="/api/land", tags=["Land Assessment & Due Diligence"])

@router.post("/assess", response_model=LandAssessResponse)
async def assess_land(payload: LandAssessRequest):
    try:
        report = await perform_land_assessment(
            address=payload.address,
            proposed_use=payload.proposed_use,
            area_sqm=payload.plot_area_sqm,
            lat=payload.latitude,
            lon=payload.longitude
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Land assessment failed: {str(e)}")
