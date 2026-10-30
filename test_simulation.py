import sys
from pathlib import Path

SOLUM_DIR = Path(__file__).resolve().parent / "SOLUM"
sys.path.insert(0, str(SOLUM_DIR))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_simulation_workflow():
    print("=== Testing SOLUM Scenario Simulation Engine ===")
    
    # 1. Create Simulation for Chennai (Velachery)
    res = client.post("/api/simulation/create", json={
        "latitude": 12.9815,
        "longitude": 80.2180,
        "location_name": "Velachery, Chennai"
    })
    assert res.status_code == 200, res.text
    meta = res.json()
    sim_id = meta["simulation_id"]
    print(f"[PASS] Created Simulation: {sim_id}")
    print(f"       Scenario: {meta['scenario_type']} - {meta['scenario_title']}")
    print(f"       Supported Scenarios: {meta['supported_scenarios']}")
    assert len(meta["supported_scenarios"]) >= 2
    assert "flood" in meta["supported_scenarios"]

    # 2. Query Metadata
    res_get = client.get(f"/api/simulation/{sim_id}")
    assert res_get.status_code == 200
    assert res_get.json()["simulation_id"] == sim_id
    print(f"[PASS] GET /api/simulation/{sim_id} verified")

    # 3. Test Hour Progression (0, 6, 12, 18, 24)
    for h in [0, 6, 12, 18, 24]:
        st_res = client.get(f"/api/simulation/{sim_id}/state?hour={h}")
        assert st_res.status_code == 200, st_res.text
        st = st_res.json()
        assert st["hour"] == h
        assert "geojson" in st
        assert len(st["geojson"]["features"]) >= 5  # polygon + 4 roads + 4 facilities
        assert len(st["roads_affected"]) >= 4
        assert len(st["critical_facilities"]) >= 4
        print(f"[PASS] Hour +{h:02d}: {st['stage_label']} | Severity: {st['severity_level']} | Rain: {st['metrics']['rainfall_accumulated_mm']}mm | Wind: {st['metrics']['peak_wind_gust_kmh']}km/h | Vol: {st['metrics']['water_accumulation_volume_m3']:,.0f}m³")

    # 4. Test Impacts Comparison
    imp_res = client.get(f"/api/simulation/{sim_id}/impacts")
    assert imp_res.status_code == 200
    impacts = imp_res.json()
    assert len(impacts["stages"]) == 5
    print(f"[PASS] Impacts endpoint returned all 5 milestone stages")

    # 5. Test Mountainous Location (Ooty / Nilgiris) -> Automatic Landslide detection
    ooty_res = client.post("/api/simulation/create", json={
        "latitude": 11.4102,
        "longitude": 76.6950,
        "location_name": "Ooty, Nilgiris"
    })
    assert ooty_res.status_code == 200
    ooty_meta = ooty_res.json()
    assert ooty_meta["scenario_type"] == "landslide", f"Expected landslide, got {ooty_meta['scenario_type']}"
    assert "landslide" in ooty_meta["supported_scenarios"]
    print(f"[PASS] Ooty (Elevation {ooty_meta['elevation_amsl']}m) correctly triggered Landslide Susceptibility Scenario: {ooty_meta['scenario_title']}")

    # 6. Test Coastal Location (Kanyakumari) -> Coastal Cyclone / Surge detection
    kk_res = client.post("/api/simulation/create", json={
        "latitude": 8.0883,
        "longitude": 77.5385,
        "location_name": "Kanyakumari Coastal"
    })
    assert kk_res.status_code == 200
    kk_meta = kk_res.json()
    assert "cyclone" in kk_meta["supported_scenarios"]
    print(f"[PASS] Kanyakumari correctly included Cyclone/Surge scenario: {kk_meta['scenario_title']}")

    # 7. Test Explicit Scenario Override (e.g. asking for 'rainfall' in Chennai)
    rf_res = client.post("/api/simulation/create", json={
        "latitude": 13.0827,
        "longitude": 80.2707,
        "scenario_type": "rainfall",
        "location_name": "Chennai Central"
    })
    assert rf_res.status_code == 200
    assert rf_res.json()["scenario_type"] == "rainfall"
    print(f"[PASS] Explicit scenario override to 'rainfall' verified")

if __name__ == "__main__":
    test_simulation_workflow()
    print("\nALL SIMULATION BACKEND TESTS PASSED PERFECTLY!")
