import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import UploadFile
from backend.config import settings
from backend.database import db_session
from backend.models import IssueResponse, IssueStatsResponse, OfficialUpdateCreate, AuditLogResponse, OfficialStatsResponse

CATEGORY_ICONS = {
    "Electricity": "bolt",
    "Drainage": "water",
    "Roads": "tree",
    "Telecom": "network",
    "Other": "tool"
}

def row_to_issue(row) -> IssueResponse:
    evidence = []
    if row["evidence_json"]:
        try:
            evidence = json.loads(row["evidence_json"])
        except Exception:
            evidence = []
    
    steps = []
    if row["steps_json"]:
        try:
            steps = json.loads(row["steps_json"])
        except Exception:
            steps = []

    r_keys = row.keys()
    return IssueResponse(
        id=row["id"],
        title=row["title"],
        place=row["place"],
        district=row["district"] if "district" in r_keys else "Chennai",
        city=row["city"] if "city" in r_keys else "Chennai",
        locality=row["locality"] if "locality" in r_keys else "Velachery",
        latitude=row["latitude"],
        longitude=row["longitude"],
        type=row["type"],
        icon=row["icon"],
        priority=row["priority"],
        status=row["status"],
        progress=row["progress"],
        crew=row["crew"],
        cost=row["cost"],
        hours=row["hours"],
        owner=row["owner"],
        reason=row["reason"],
        dependency=row["dependency"],
        update=row["latest_update"],
        steps=steps,
        risk=row["risk_advisory"],
        evidence=evidence,
        data_source=row["data_source"] if "data_source" in r_keys else "Demonstration baseline (SOLUM)",
        record_type=row["record_type"] if "record_type" in r_keys else "demonstration",
        local=bool(row["is_local_submission"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

def list_issues(
    status: Optional[str] = None,
    category: Optional[str] = None,
    district: Optional[str] = None,
    locality: Optional[str] = None,
    city: Optional[str] = None,
    record_type: Optional[str] = None
) -> List[IssueResponse]:
    query = "SELECT * FROM issues WHERE 1=1"
    params = []
    if status and status != "all":
        if status == "open":
            query += " AND status != 'Resolved'"
        else:
            query += " AND status = ?"
            params.append(status)
    if category and category != "all":
        query += " AND type = ?"
        params.append(category)
    if record_type and record_type != "all":
        query += " AND record_type = ?"
        params.append(record_type)

    if district and district.lower() not in ("all", "tamil nadu", "tamilnadu", "india"):
        query += " AND (LOWER(district) = LOWER(?) OR LOWER(city) = LOWER(?) OR LOWER(place) LIKE ?)"
        params.extend([district, district, f"%{district.lower()}%"])

    if locality and locality.lower() not in ("all",):
        query += " AND (LOWER(locality) = LOWER(?) OR LOWER(place) LIKE ?)"
        params.extend([locality, f"%{locality.lower()}%"])

    if city and city.lower() not in ("all",):
        query += " AND (LOWER(city) = LOWER(?) OR LOWER(place) LIKE ?)"
        params.extend([city, f"%{city.lower()}%"])

    query += " ORDER BY created_at DESC"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [row_to_issue(r) for r in rows]

def get_issue_by_id(issue_id: str) -> Optional[IssueResponse]:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
        return row_to_issue(row) if row else None

def get_issue_stats(
    district: Optional[str] = None,
    locality: Optional[str] = None,
    city: Optional[str] = None
) -> IssueStatsResponse:
    base_query = "SELECT COUNT(*) FROM issues WHERE 1=1"
    params = []
    if district and district.lower() not in ("all", "tamil nadu", "tamilnadu", "india"):
        base_query += " AND (LOWER(district) = LOWER(?) OR LOWER(city) = LOWER(?) OR LOWER(place) LIKE ?)"
        params.extend([district, district, f"%{district.lower()}%"])
    if locality and locality.lower() not in ("all",):
        base_query += " AND (LOWER(locality) = LOWER(?) OR LOWER(place) LIKE ?)"
        params.extend([locality, f"%{locality.lower()}%"])
    if city and city.lower() not in ("all",):
        base_query += " AND (LOWER(city) = LOWER(?) OR LOWER(place) LIKE ?)"
        params.extend([city, f"%{city.lower()}%"])

    with db_session() as conn:
        total = conn.execute(base_query, params).fetchone()[0]
        in_progress = conn.execute(base_query + " AND status = 'In progress'", params).fetchone()[0]
        resolved = conn.execute(base_query + " AND status = 'Resolved'", params).fetchone()[0]
        awaiting = total - in_progress - resolved
        return IssueStatsResponse(
            total=total,
            in_progress=in_progress,
            resolved=resolved,
            awaiting=awaiting,
            district=district,
            locality=locality
        )

async def create_issue_with_files(
    subject: str,
    category: str,
    place: str,
    description: str,
    district: Optional[str] = None,
    city: Optional[str] = None,
    locality: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    files: Optional[List[UploadFile]] = None
) -> IssueResponse:
    now = datetime.now(timezone.utc).isoformat()
    issue_id = f"SLM-{datetime.now().strftime('%M%S%f')[:7]}"
    icon = CATEGORY_ICONS.get(category, "tool")

    # Auto-resolve district and locality from coordinates if missing
    if not district and latitude is not None and longitude is not None:
        try:
            from backend.data.tamil_nadu_gis import find_nearest_district
            d_name, _, _ = find_nearest_district(latitude, longitude)
            district = d_name
        except Exception:
            district = "Tamil Nadu"
    if not district:
        district = "Chennai"
    if not city:
        city = district
    if not locality:
        locality = place.split(",")[0].strip() if "," in place else place

    evidence_filenames = []
    if files:
        for f in files:
            if not f.filename:
                continue
            ext = os.path.splitext(f.filename)[1]
            saved_name = f"{uuid.uuid4().hex[:10]}{ext}"
            file_path = settings.UPLOAD_DIR / saved_name
            content = await f.read()
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            evidence_filenames.append(f.filename)

    steps = [
        "Complaint registered in SOLUM database",
        "Field inspection and safety triage pending",
        "Crew & contractor assignment pending",
        "Work verification and closure pending"
    ]

    with db_session() as conn:
        conn.execute("""
        INSERT INTO issues (
            id, title, place, district, city, locality, latitude, longitude, type, icon, priority, status,
            progress, crew, cost, hours, owner, reason, dependency, latest_update,
            steps_json, risk_advisory, evidence_json, data_source, record_type, is_local_submission,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            issue_id,
            subject.strip(),
            place.strip(),
            district,
            city,
            locality,
            latitude or 12.9815,
            longitude or 80.2180,
            category,
            icon,
            "Unassessed",
            "Assessment",
            0,
            0,
            0,
            0,
            "Awaiting dispatch lead",
            "Logged via citizen complaint dialog; pending inspection.",
            "Field verification required",
            description.strip(),
            json.dumps(steps),
            "Do not enter cordoned or active danger areas to capture evidence.",
            json.dumps(evidence_filenames),
            "Citizen complaint (SOLUM Portal)",
            "user-submitted",
            1,
            now,
            now
        ))

    return get_issue_by_id(issue_id)

def get_prioritized_issues(
    district: Optional[str] = None,
    city: Optional[str] = None,
    locality: Optional[str] = None,
    status: Optional[str] = "all"
) -> List[IssueResponse]:
    """Sort issues for the location: Life-safety -> dependencies -> access -> general restoration."""
    issues_list = list_issues(status=status, district=district, city=city, locality=locality)
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Unassessed": 3}
    def sort_key(x):
        is_resolved = 1 if x.status == "Resolved" else 0
        p_rank = priority_order.get(x.priority, 3)
        return (is_resolved, p_rank)
    return sorted(issues_list, key=sort_key)

def get_official_dashboard_stats(
    district: Optional[str] = None,
    city: Optional[str] = None,
    locality: Optional[str] = None
) -> OfficialStatsResponse:
    """Computes comprehensive location-scoped statistics for the Officials workspace."""
    base_query = "SELECT * FROM issues WHERE 1=1"
    params = []
    if district and district.lower() not in ("all", "all-tn", "tamil nadu", "tamilnadu", "india"):
        base_query += " AND (LOWER(district) = LOWER(?) OR LOWER(city) = LOWER(?) OR LOWER(place) LIKE ?)"
        params.extend([district, district, f"%{district.lower()}%"])
    if locality and locality.lower() not in ("all",):
        base_query += " AND (LOWER(locality) = LOWER(?) OR LOWER(place) LIKE ?)"
        params.extend([locality, f"%{locality.lower()}%"])
    if city and city.lower() not in ("all",):
        base_query += " AND (LOWER(city) = LOWER(?) OR LOWER(place) LIKE ?)"
        params.extend([city, f"%{city.lower()}%"])

    with db_session() as conn:
        rows = conn.execute(base_query, params).fetchall()
        
    total = len(rows)
    pending = sum(1 for r in rows if r["status"] in ("Assessment", "Assigned"))
    in_progress = sum(1 for r in rows if r["status"] == "In progress")
    resolved = sum(1 for r in rows if r["status"] == "Resolved")
    critical = sum(1 for r in rows if r["priority"] == "Critical")
    
    # Open issues metrics
    open_rows = [r for r in rows if r["status"] != "Resolved"]
    total_cost = sum(r["cost"] for r in open_rows)
    total_crew = sum(r["crew"] for r in open_rows)
    teams = len(set(r["owner"] for r in open_rows if r["owner"] and "Awaiting" not in r["owner"]))
    avg_progress = int(sum(r["progress"] for r in open_rows) / len(open_rows)) if open_rows else 0
    
    return OfficialStatsResponse(
        total_reported=total,
        pending_issues=pending,
        in_progress=in_progress,
        resolved=resolved,
        critical_priority=critical,
        assigned_teams=teams,
        repair_progress_avg=avg_progress,
        total_cost=total_cost,
        total_crew=total_crew,
        district=district or "All Tamil Nadu",
        locality=locality
    )

def apply_official_update(update: OfficialUpdateCreate) -> IssueResponse:
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        existing = conn.execute("SELECT * FROM issues WHERE id = ?", (update.issue_id,)).fetchone()
        if not existing:
            raise ValueError(f"Issue {update.issue_id} not found")

        progress = 100 if update.status == "Resolved" else min(99, update.progress)

        conn.execute("""
        UPDATE issues
        SET status = ?, progress = ?, crew = ?, cost = ?, hours = ?,
            owner = ?, latest_update = ?, updated_at = ?
        WHERE id = ?
        """, (
            update.status,
            progress,
            update.crew,
            update.cost,
            update.hours,
            update.owner,
            update.note,
            now,
            update.issue_id
        ))

        # Log into audit_logs
        conn.execute("""
        INSERT INTO audit_logs (issue_id, status, note, actor_role, crew_allocated, cost_allocated, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            update.issue_id,
            update.status,
            update.note,
            update.actor_role,
            update.crew,
            update.cost,
            now
        ))

    return get_issue_by_id(update.issue_id)

def get_audit_logs(limit: int = 15) -> List[AuditLogResponse]:
    with db_session() as conn:
        rows = conn.execute("""
        SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
        return [
            AuditLogResponse(
                id=r["id"],
                issue_id=r["issue_id"],
                status=r["status"],
                note=r["note"],
                actor_role=r["actor_role"],
                crew_allocated=r["crew_allocated"],
                cost_allocated=r["cost_allocated"],
                created_at=r["created_at"]
            ) for r in rows
        ]
