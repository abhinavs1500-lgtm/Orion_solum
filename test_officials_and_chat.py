import sys
import os
from pathlib import Path

# Add SOLUM directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "SOLUM"))

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.officials_auth import (
    authenticate_official,
    verify_official_token,
    check_official_jurisdiction,
    OFFICIAL_CREDENTIALS
)
from backend.models import OfficialLoginRequest

client = TestClient(app)

def test_svg_assets_exist():
    print("\n--- TEST: Image Assets Integrity ---")
    news_dir = Path("SOLUM/assets/images/news")
    cat_dir = Path("SOLUM/assets/images/categories")
    
    expected_news = [
        "waterbody-restoration.svg", "stormwater-drainage.svg", "monsoon-radar.svg",
        "urban-planning.svg", "hill-slope.svg", "coastal-resilience.svg", "power-grid.svg"
    ]
    expected_cats = [
        "electrical.svg", "waterlogging.svg", "road-damage.svg",
        "fallen-trees.svg", "drainage.svg", "public-infra.svg"
    ]
    
    for fname in expected_news:
        p = news_dir / fname
        assert p.exists(), f"Missing news SVG: {fname}"
        content = p.read_text(encoding='utf-8')
        assert "<svg" in content and "</svg>" in content, f"Invalid SVG markup in {fname}"
    print(f" [PASS] All {len(expected_news)} news SVGs verified.")

    for fname in expected_cats:
        p = cat_dir / fname
        assert p.exists(), f"Missing category SVG: {fname}"
        content = p.read_text(encoding='utf-8')
        assert "<svg" in content and "</svg>" in content, f"Invalid SVG markup in {fname}"
    print(f" [PASS] All {len(expected_cats)} category SVGs verified.")

def test_officials_authentication_flow():
    print("\n--- TEST: Officials Authentication & Token Flow ---")
    # 1. Correct credentials
    req = OfficialLoginRequest(
        official_id="OFF-CH-02",
        passcode="SOLUM-TN-2026",
        role="District coordination officer",
        district="Chennai"
    )
    auth = authenticate_official(req)
    assert auth.token is not None and "." in auth.token
    assert auth.district == "Chennai"
    assert auth.official_id == "OFF-CH-02"
    print(" [PASS] Direct service authentication succeeded.")

    # 2. Token verification
    payload = verify_official_token(auth.token)
    assert payload["oid"] == "OFF-CH-02"
    assert payload["district"] == "Chennai"
    print(" [PASS] HMAC-SHA256 token verification verified.")

    # 3. Invalid passcode
    bad_req = OfficialLoginRequest(
        official_id="OFF-CH-02",
        passcode="WRONG-PASSWORD"
    )
    try:
        authenticate_official(bad_req)
        assert False, "Should have rejected bad password"
    except Exception as e:
        assert getattr(e, "status_code", None) == 401
        print(" [PASS] Bad password rejected with 401 Unauthorized.")

    # 4. HTTP API Login
    res = client.post("/api/officials/login", json={
        "official_id": "OFF-CB-03",
        "passcode": "SOLUM-TN-2026"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["district"] == "Coimbatore"
    assert data["name"] == "Er. P. Shanmugam"
    print(" [PASS] POST /api/officials/login endpoint verified.")

    # 5. HTTP API Verify
    res_v = client.get(f"/api/officials/verify?token={data['token']}")
    assert res_v.status_code == 200
    v_data = res_v.json()
    assert v_data["active"] is True
    assert v_data["district"] == "Coimbatore"
    print(" [PASS] GET /api/officials/verify endpoint verified.")

def test_officials_location_scoped_priorities_and_stats():
    print("\n--- TEST: Location-Scoped Priorities & Stats ---")
    # Chennai priorities
    res_ch = client.get("/api/officials/priorities?district=Chennai")
    assert res_ch.status_code == 200
    ch_items = res_ch.json()
    assert len(ch_items) > 0
    print(f" [PASS] Chennai priorities count: {len(ch_items)}")

    # Coimbatore priorities
    res_cb = client.get("/api/officials/priorities?district=Coimbatore")
    assert res_cb.status_code == 200
    cb_items = res_cb.json()
    assert len(cb_items) > 0
    # Confirm Coimbatore items reflect Coimbatore locality/district
    assert any(i.get("district") == "Coimbatore" or "Coimbatore" in (i.get("place") or "") for i in cb_items)
    print(f" [PASS] Coimbatore priorities count: {len(cb_items)}")

    # Madurai priorities
    res_md = client.get("/api/officials/priorities?district=Madurai")
    assert res_md.status_code == 200
    md_items = res_md.json()
    assert len(md_items) > 0
    print(f" [PASS] Madurai priorities count: {len(md_items)}")

    # Official stats endpoint
    res_st = client.get("/api/officials/stats?district=Chennai")
    assert res_st.status_code == 200
    st_data = res_st.json()
    assert "total_reported" in st_data
    assert "in_progress" in st_data
    assert "resolved" in st_data
    assert "critical_priority" in st_data
    assert "repair_progress_avg" in st_data
    assert st_data["district"] == "Chennai"
    print(f" [PASS] Officials stats for Chennai: Total={st_data['total_reported']}, Critical={st_data['critical_priority']}, Progress={st_data['repair_progress_avg']}%")

def test_jurisdiction_authorization_enforcement():
    print("\n--- TEST: Jurisdiction Authorization Enforcement ---")
    # 1. Login as Coimbatore Officer
    res_cb = client.post("/api/officials/login", json={
        "official_id": "OFF-CB-03",
        "passcode": "SOLUM-TN-2026"
    })
    token_cb = res_cb.json()["token"]

    # 2. Attempt to modify Chennai issue (SLM-1042) -> Should be rejected with 403 Forbidden
    res_unauth = client.post(
        "/api/officials/updates",
        headers={"X-Official-Token": token_cb},
        json={
            "issue_id": "SLM-1042",
            "status": "In progress",
            "progress": 55,
            "crew": 8,
            "cost": 240000,
            "hours": 6,
            "owner": "Electricity response team",
            "note": "Cross-jurisdiction test update attempt",
            "actor_role": "District coordination officer"
        }
    )
    assert res_unauth.status_code == 403, f"Expected 403, got {res_unauth.status_code}: {res_unauth.text}"
    assert "jurisdiction" in res_unauth.json()["detail"].lower()
    print(" [PASS] Cross-district modification blocked with 403 Forbidden.")

    # 3. Login as Chennai Officer
    res_ch = client.post("/api/officials/login", json={
        "official_id": "OFF-CH-02",
        "passcode": "SOLUM-TN-2026"
    })
    token_ch = res_ch.json()["token"]

    # 4. Chennai officer modifying Chennai issue -> Should succeed (200 OK)
    res_auth = client.post(
        "/api/officials/updates",
        headers={"X-Official-Token": token_ch},
        json={
            "issue_id": "SLM-1042",
            "status": "In progress",
            "progress": 50,
            "crew": 8,
            "cost": 240000,
            "hours": 6,
            "owner": "TANGEDCO Emergency Team",
            "note": "Authorized Chennai official isolation progress update.",
            "actor_role": "District coordination officer"
        }
    )
    assert res_auth.status_code == 200, res_auth.text
    assert res_auth.json()["progress"] == 50
    print(" [PASS] Authorized district official update succeeded.")

    # 5. State Commissioner (All-TN) modifying any district -> Should succeed (200 OK)
    res_tn = client.post("/api/officials/login", json={
        "official_id": "OFF-TN-01",
        "passcode": "SOLUM-TN-2026"
    })
    token_tn = res_tn.json()["token"]
    res_comm = client.post(
        "/api/officials/updates",
        headers={"X-Official-Token": token_tn},
        json={
            "issue_id": "SLM-1042",
            "status": "In progress",
            "progress": 52,
            "crew": 8,
            "cost": 240000,
            "hours": 6,
            "owner": "TANGEDCO Emergency Team",
            "note": "State Commissioner statewide administrative review.",
            "actor_role": "State Disaster Commissioner"
        }
    )
    assert res_comm.status_code == 200, res_comm.text
    print(" [PASS] State Disaster Commissioner (All-TN jurisdiction) statewide update succeeded.")

def test_solum_ai_conversational_engine():
    print("\n--- TEST: SOLUM AI Conversational Engine ---")
    # 1. District comparison
    res1 = client.post("/api/chat", json={
        "message": "Compare flood risks between Madurai and Chennai",
        "history": [],
        "location": {"name": "Madurai", "district": "Madurai", "state": "Tamil Nadu", "lat": 9.9252, "lon": 78.1198}
    })
    assert res1.status_code == 200
    d1 = res1.json()
    assert "madurai" in d1["reply"].lower() and "chennai" in d1["reply"].lower()
    assert len(d1.get("actions", [])) > 0
    print(" [PASS] District comparison response generated with actionable buttons.")

    # 2. Multi-turn context resolution
    history = [
        {"role": "user", "content": "I am in Madurai."},
        {"role": "assistant", "content": "Welcome to Madurai."}
    ]
    res2 = client.post("/api/chat", json={
        "message": "What are the common hazards here during monsoons?",
        "history": history,
        "location": {"name": "Madurai", "district": "Madurai", "state": "Tamil Nadu", "lat": 9.9252, "lon": 78.1198}
    })
    assert res2.status_code == 200
    d2 = res2.json()
    assert "vaigai" in d2["reply"].lower() or "madurai" in d2["reply"].lower() or "tank" in d2["reply"].lower()
    print(" [PASS] Multi-turn conversational context successfully tracks location.")

    # 3. Technical explanation: elevation vs slope
    res3 = client.post("/api/chat", json={
        "message": "What is the difference between elevation and slope in land assessment?",
        "history": [],
        "location": {"name": "Chennai", "lat": 13.0827, "lon": 80.2707}
    })
    assert res3.status_code == 200
    d3 = res3.json()
    assert "elevation" in d3["reply"].lower() and "slope" in d3["reply"].lower()
    print(" [PASS] Technical terrain explanation generated.")

    # 4. Contextual explanation of user's land assessment
    res4 = client.post("/api/chat", json={
        "message": "Can you explain my land assessment?",
        "history": [],
        "location": {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
        "context": {
            "current_page": "report",
            "last_assessment": {
                "address": "Gandhipuram, Coimbatore",
                "elevation_m": 411.5,
                "slope_percent": 1.8,
                "distance_to_water_m": 350.0,
                "overall_readiness": "Proceed with site-specific survey",
                "summary_note": "Favorable elevation with moderate drainage distance."
            }
        }
    })
    assert res4.status_code == 200
    d4 = res4.json()
    assert "411" in d4["reply"] or "gandhipuram" in d4["reply"].lower() or "coimbatore" in d4["reply"].lower()
    print(" [PASS] Land assessment context grounded in user data.")

def test_news_images_integration():
    print("\n--- TEST: News Service Illustrative Images ---")
    res = client.get("/api/news?region=Chennai&scope=district")
    assert res.status_code == 200
    data = res.json()
    items = data.get("items", [])
    assert len(items) > 0
    for it in items:
        assert "image_url" in it and it["image_url"].startswith("assets/images/news/")
        assert "image_caption" in it and len(it["image_caption"]) > 0
    print(f" [PASS] Verified news items ({len(items)}) have valid local illustrative image URLs and captions.")

if __name__ == "__main__":
    test_svg_assets_exist()
    test_officials_authentication_flow()
    test_officials_location_scoped_priorities_and_stats()
    test_jurisdiction_authorization_enforcement()
    test_solum_ai_conversational_engine()
    test_news_images_integration()
    print("\n==============================================")
    print(" ALL OFFICIAL ACCESS & SOLUM AI TESTS PASSED! ")
    print("==============================================\n")
