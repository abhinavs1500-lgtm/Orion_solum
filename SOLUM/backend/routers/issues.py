from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from backend.models import IssueResponse, IssueStatsResponse
from backend.services.issues_service import (
    list_issues,
    get_issue_by_id,
    get_issue_stats,
    create_issue_with_files
)

router = APIRouter(prefix="/api/issues", tags=["Civic Issues & Repairs"])
complaints_router = APIRouter(prefix="/api/complaints", tags=["Civic Complaints"])

def _get_issues_handler(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    locality: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    record_type: Optional[str] = Query(None)
):
    return list_issues(
        status=status,
        category=category,
        district=district,
        locality=locality,
        city=city,
        record_type=record_type
    )

def _get_stats_handler(
    district: Optional[str] = Query(None),
    locality: Optional[str] = Query(None),
    city: Optional[str] = Query(None)
):
    return get_issue_stats(district=district, locality=locality, city=city)

def _get_issue_handler(issue_id: str):
    issue = get_issue_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return issue

async def _submit_complaint_handler(
    subject: str = Form(..., min_length=3, max_length=150),
    category: str = Form(...),
    place: str = Form(..., min_length=2, max_length=160),
    description: str = Form(..., min_length=10, max_length=1000),
    district: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    locality: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    evidence: Optional[List[UploadFile]] = File(None)
):
    try:
        created = await create_issue_with_files(
            subject=subject,
            category=category,
            place=place,
            description=description,
            district=district,
            city=city,
            locality=locality,
            latitude=latitude,
            longitude=longitude,
            files=evidence
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit complaint: {str(e)}")

# Mount handlers on both /api/issues and /api/complaints
router.add_api_route("", _get_issues_handler, methods=["GET"], response_model=List[IssueResponse])
router.add_api_route("/stats", _get_stats_handler, methods=["GET"], response_model=IssueStatsResponse)
router.add_api_route("/{issue_id}", _get_issue_handler, methods=["GET"], response_model=IssueResponse)
router.add_api_route("", _submit_complaint_handler, methods=["POST"], response_model=IssueResponse)

complaints_router.add_api_route("", _get_issues_handler, methods=["GET"], response_model=List[IssueResponse])
complaints_router.add_api_route("/stats", _get_stats_handler, methods=["GET"], response_model=IssueStatsResponse)
complaints_router.add_api_route("/{issue_id}", _get_issue_handler, methods=["GET"], response_model=IssueResponse)
complaints_router.add_api_route("", _submit_complaint_handler, methods=["POST"], response_model=IssueResponse)
