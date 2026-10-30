import sys
from pathlib import Path

# Add SOLUM directory to sys.path
SOLUM_DIR = Path(__file__).resolve().parent / "SOLUM"
sys.path.insert(0, str(SOLUM_DIR))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "ok"
    assert data["app"] == "SOLUM"
    assert data["maps_3d_configured"] is True
    print("[PASS] Health endpoint verified")

def test_maps_config():
    res = client.get("/api/maps/config")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["api_key"] != ""
    assert data["default_center"]["lat"] == 13.0827
    print("[PASS] Maps 3D config verified")

def test_maps_location_context():
    res = client.post("/api/maps/location-context", json={"latitude": 12.9815, "longitude": 80.2180})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "elevation_m" in data
    assert "flood_zone" in data
    assert len(data["nearby_issues"]) > 0
    print("[PASS] Maps 3D location context verified")

def test_weather():
    res = client.get("/api/weather?lat=13.0827&lon=80.2707")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "daily" in data
    assert "current" in data
    assert "receipt_sha256" in data
    print("[PASS] Weather endpoint & SHA-256 receipt verified")

def test_geocode():
    res = client.get("/api/geocode?q=Chennai")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "results" in data
    assert len(data["results"]) > 0
    print("[PASS] Geocoding verified")

def test_news():
    res = client.get("/api/news?region=Chennai&scope=district")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert len(data["items"]) > 0
    print("[PASS] News endpoint verified")

def test_issues_and_stats():
    res = client.get("/api/issues")
    assert res.status_code == 200, res.text
    issues = res.json()
    assert len(issues) >= 5
    
    stats_res = client.get("/api/issues/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total"] >= 5
    print("[PASS] Issues list and stats counters verified")

def test_complaint_submission():
    payload = {
        "subject": "Fallen transmission wire near park",
        "category": "Electricity",
        "place": "100 Feet Road, Velachery",
        "description": "High voltage line sparking after rain storm; requires immediate isolation.",
        "latitude": 12.9780,
        "longitude": 80.2195
    }
    res = client.post("/api/issues", data=payload)
    assert res.status_code == 200, res.text
    created = res.json()
    assert created["id"].startswith("SLM-")
    assert created["title"] == payload["subject"]
    print(f"[PASS] Complaint creation verified: {created['id']}")

def test_officials_workflow():
    p_res = client.get("/api/officials/priorities")
    assert p_res.status_code == 200
    priorities = p_res.json()
    assert len(priorities) > 0
    
    first_issue = priorities[0]["id"]
    # Authenticate as authorized State Disaster Commissioner (All-TN jurisdiction)
    login_res = client.post("/api/officials/login", json={
        "official_id": "OFF-TN-01",
        "passcode": "SOLUM-TN-2026"
    })
    token = login_res.json()["token"]

    update_res = client.post("/api/officials/updates", headers={"X-Official-Token": token}, json={
        "issue_id": first_issue,
        "status": "In progress",
        "progress": 60,
        "crew": 10,
        "cost": 300000,
        "hours": 5,
        "owner": "Emergency Grid Unit",
        "note": "Backup transformer staged and live isolation confirmed.",
        "actor_role": "District coordination officer"
    })
    assert update_res.status_code == 200
    
    audit_res = client.get("/api/officials/audit")
    assert audit_res.status_code == 200
    audits = audit_res.json()
    assert len(audits) > 0
    assert audits[0]["issue_id"] == first_issue

    plan_res = client.get("/api/officials/plan/export?available_funds=1200000&available_crew=30")
    assert plan_res.status_code == 200
    plan = plan_res.json()
    assert plan["available_funds_inr"] == 1200000
    print("[PASS] Officials priorities, update publishing, audit logging, and plan export verified")

def test_land_assessment():
    res = client.post("/api/land/assess", json={
        "address": "Velachery Main Road, Chennai",
        "proposed_use": "Apartment building",
        "plot_area_sqm": 850,
        "latitude": 12.9815,
        "longitude": 80.2180
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["report_id"].startswith("LND-")
    assert data["elevation_m"] > 0
    assert data["flood_risk_level"] in ["Low", "Moderate", "High", "Severe"]
    assert len(data["matrix"]) == 6
    print("[PASS] Land assessment due-diligence pipeline verified")

def test_chat():
    res = client.post("/api/chat", json={
        "message": "What should I pack in an emergency kit?",
        "location": {"name": "Chennai", "lat": 12.9815, "lon": 80.2180}
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "reply" in data
    assert "IMD" in data["source_title"] or "NDMA" in data["source_title"]
    print("[PASS] Grounded AI chat advisor verified")

def test_static_pages():
    for page in ["/", "/index.html", "/prepare.html", "/resolve.html", "/officials.html", "/report.html"]:
        res = client.get(page)
        assert res.status_code == 200, f"Page {page} failed"
    print("[PASS] All 5 HTML pages served successfully")

if __name__ == "__main__":
    print("=== Running SOLUM Backend Verification Suite ===")
    test_health()
    test_maps_config()
    test_maps_location_context()
    test_weather()
    test_geocode()
    test_news()
    test_issues_and_stats()
    test_complaint_submission()
    test_officials_workflow()
    test_land_assessment()
    test_chat()
    test_static_pages()
    print("\nALL 12 TEST SUITES PASSED PERFECTLY!")
