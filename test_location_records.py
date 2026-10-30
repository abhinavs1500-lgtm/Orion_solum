import sys
from pathlib import Path

SOLUM_DIR = Path(__file__).resolve().parent / "SOLUM"
sys.path.insert(0, str(SOLUM_DIR))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_location_filtering():
    print("--- 1. Testing District & Locality Complaint Queries ---")
    
    # Coimbatore
    res = client.get("/api/complaints?district=Coimbatore")
    assert res.status_code == 200
    cbe_data = res.json()
    assert len(cbe_data) == 2, f"Expected 2 for Coimbatore, got {len(cbe_data)}"
    assert all(item.get("district") == "Coimbatore" for item in cbe_data)
    print(f"[PASS] Coimbatore: {len(cbe_data)} complaints (Singanallur, RS Puram)")

    # Madurai
    res = client.get("/api/complaints?district=Madurai")
    assert res.status_code == 200
    mdu_data = res.json()
    assert len(mdu_data) == 2
    assert all(item.get("district") == "Madurai" for item in mdu_data)
    print(f"[PASS] Madurai: {len(mdu_data)} complaints (Goripalayam, Mattuthavani)")

    # Salem
    res = client.get("/api/complaints?district=Salem")
    assert res.status_code == 200
    slm_data = res.json()
    assert len(slm_data) == 1
    assert slm_data[0]["locality"] == "Hasthampatti"
    print(f"[PASS] Salem: {len(slm_data)} complaint (Hasthampatti)")

    # Tiruchirappalli
    res = client.get("/api/complaints?district=Tiruchirappalli")
    assert res.status_code == 200
    try_data = res.json()
    assert len(try_data) == 1
    assert try_data[0]["locality"] == "Srirangam"
    print(f"[PASS] Tiruchirappalli: {len(try_data)} complaint (Srirangam)")

    # Nilgiris (Ooty)
    res = client.get("/api/complaints?district=Nilgiris")
    assert res.status_code == 200
    ooty_data = res.json()
    assert len(ooty_data) == 1
    assert ooty_data[0]["locality"] == "Ooty"
    print(f"[PASS] Nilgiris (Ooty): {len(ooty_data)} complaint (Ooty Coonoor Road)")

    # Kanyakumari
    res = client.get("/api/complaints?district=Kanyakumari")
    assert res.status_code == 200
    kk_data = res.json()
    assert len(kk_data) == 1
    assert kk_data[0]["locality"] == "Kanyakumari"
    print(f"[PASS] Kanyakumari: {len(kk_data)} complaint (Kovalam Beach Road)")

    # Chennai Localities
    res = client.get("/api/complaints?locality=Velachery")
    assert res.status_code == 200
    vel_data = res.json()
    assert len(vel_data) >= 3
    print(f"[PASS] Velachery locality: {len(vel_data)} complaints (includes user-submitted and demo)")

    res = client.get("/api/complaints?locality=Anna Nagar")
    assert res.status_code == 200
    an_data = res.json()
    assert len(an_data) == 1
    print(f"[PASS] Anna Nagar locality: {len(an_data)} complaint")

    # Empty district (Erode)
    res = client.get("/api/complaints?district=Erode")
    assert res.status_code == 200
    er_data = res.json()
    assert len(er_data) == 0, f"Expected 0 for Erode, got {len(er_data)}"
    print("[PASS] Erode: 0 complaints (triggers clean empty state UI)")

def test_location_stats():
    print("\n--- 2. Testing District & Locality Stats Endpoints ---")
    
    # Coimbatore stats
    res = client.get("/api/complaints/stats?district=Coimbatore")
    assert res.status_code == 200
    s_cbe = res.json()
    assert s_cbe["total"] == 2
    assert s_cbe["in_progress"] == 1
    assert s_cbe["awaiting"] == 1
    print(f"[PASS] Coimbatore stats: {s_cbe}")

    # Madurai stats
    res = client.get("/api/complaints/stats?district=Madurai")
    assert res.status_code == 200
    s_mdu = res.json()
    assert s_mdu["total"] == 2
    assert s_mdu["in_progress"] == 1
    assert s_mdu["awaiting"] == 1
    print(f"[PASS] Madurai stats: {s_mdu}")

    # Erode stats
    res = client.get("/api/complaints/stats?district=Erode")
    assert res.status_code == 200
    s_er = res.json()
    assert s_er["total"] == 0
    assert s_er["in_progress"] == 0
    assert s_er["resolved"] == 0
    assert s_er["awaiting"] == 0
    print(f"[PASS] Erode stats (zeroed counters): {s_er}")

def test_geospatial_context_all_tn():
    print("\n--- 3. Testing Real Geospatial Intelligence across Tamil Nadu ---")
    locations = [
        ("Chennai (Velachery)", 12.9815, 80.2180, "Zone III"),
        ("Coimbatore", 11.0168, 76.9558, "Zone III"),
        ("Madurai", 9.9252, 78.1198, "Zone II"),
        ("Ooty (Nilgiris)", 11.4102, 76.6950, "Zone II"),
        ("Kanyakumari", 8.0883, 77.5385, "Zone II"),
        ("Salem", 11.6643, 78.1460, "Zone III"),
        ("Tiruchirappalli", 10.7905, 78.7047, "Zone II")
    ]
    for name, lat, lon, exp_seismic in locations:
        res = client.post("/api/maps/location-context", json={"latitude": lat, "longitude": lon})
        assert res.status_code == 200
        ctx = res.json()
        assert "elevation_m" in ctx
        assert "flood_zone" in ctx
        assert "water_corridors" in ctx
        
        # Land assessment for soil and seismic
        land_res = client.post("/api/land/assess", json={
            "address": name,
            "proposed_use": "Residential layout",
            "plot_area_sqm": 500,
            "latitude": lat,
            "longitude": lon
        })
        assert land_res.status_code == 200
        land_data = land_res.json()
        assert len(land_data["matrix"]) == 6
        
        # Verify IS 1893 seismic zone in zoning notes
        zoning_row = next(r for r in land_data["matrix"] if r["layer"] == "Zoning & Structural Rules")
        assert exp_seismic in zoning_row["findings"], f"Expected {exp_seismic} in {zoning_row['findings']}"
        
        soil_row = next(r for r in land_data["matrix"] if r["layer"] == "Soil & Foundation")
        print(f"[PASS] {name}: Elev {ctx['elevation_m']}m, Flood: {ctx['flood_zone']}, Soil: {soil_row['status']}, Seismic: {exp_seismic}")

if __name__ == "__main__":
    test_location_filtering()
    test_location_stats()
    test_geospatial_context_all_tn()
    print("\n=== ALL REGIONAL & LOCATION-SPECIFIC TESTS PASSED! ===")
