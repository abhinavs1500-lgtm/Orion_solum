# SOLUM — Data Sources & Geospatial Intelligence Transparency Report

## 1. Executive Summary

**SOLUM** is a full-stack geospatial intelligence and disaster preparedness platform for Tamil Nadu. This document provides complete transparency regarding the datasets, APIs, models, and demonstration records used across SOLUM's four interactive views:
- **Prepare**: Grounded hazards, elevation models, live weather forecasts, and emergency supplies.
- **Resolve**: Geographically filtered civic complaint tracking, repair milestones, and field audits.
- **Report**: Automated land due-diligence reports assessing flood risk, soil types, water buffers, and seismic regulations.
- **Officials**: Resource allocation optimizer, budget dispatching, and audit logging.

SOLUM adheres strictly to a **zero-fabrication** policy: public administrative datasets are sourced directly from verified government standards, and demonstration records are clearly partitioned and tagged from citizen submissions.

---

## 2. Verified Public Data Sources

| Domain | Dataset / Authority | Coverage & Accuracy | How SOLUM Uses It |
| :--- | :--- | :--- | :--- |
| **Elevation & Terrain** | **Copernicus DEM (30m GLO-30)** via Open-Meteo Elevation API | High-resolution 30-meter global elevation dataset from the European Space Agency (ESA) & Airbus. | Computes accurate Above Mean Sea Level (AMSL) elevations for any coordinate in Tamil Nadu. Detects depression zones and slope percentages. |
| **Hydrology & Water Buffers** | **India-WRIS** (Water Resources Information System, Ministry of Jal Shakti) & **Tamil Nadu Water Resources Department (WRD / PWD)** | 52+ verified major rivers (Cauvery, Vaigai, Bhavani, Tamirabarani, Palar, etc.), reservoirs (Chembarambakkam, Mettur, Sholayar, etc.), and protected wetland sanctuaries (Pallikaranai, Point Calimere, Kazhuveli). | Calculates geodesic proximity to water bodies, alerts against statutory 50m riparian buffer violations, and renders polygon/linestring overlays in 3D. |
| **Soil & Foundation** | **Geological Survey of India (GSI)** & **Tamil Nadu Agricultural University (TNAU) Soil Resource Atlas** | District-by-district pedological classifications across all 38 districts of Tamil Nadu. | Evaluates expansive Black Cotton soils (Vertisols in Coimbatore/Tiruppur), laterite soils in Nilgiris/Western Ghats, alluvial sands along coastal belts, and stable red loams in central plains. |
| **Seismic Hazards** | **Bureau of Indian Standards (BIS) — IS 1893:2016** (*Criteria for Earthquake Resistant Design of Structures*) | Official seismic zonation map of India (Zones II through V). | Classifies Tamil Nadu districts into Zone II (Low hazard, e.g., Madurai, Tiruchirappalli, Kanyakumari) and Zone III (Moderate hazard, e.g., Chennai, Coimbatore, Salem, Tiruvallur). |
| **Hill Area Conservation** | **Hill Area Conservation Authority (HACA)** & GSI Landslide Susceptibility Atlas | Western Ghats and Eastern Ghats mountainous tracts. | Triggers mandatory slope stability, cut-and-fill retaining wall audits, and HACA regulatory notices for Nilgiris, Kodaikanal (Dindigul), Valparai (Coimbatore), and Shevaroy Hills (Salem). |
| **Coastal Regulation** | **Tamil Nadu Coastal Zone Management Authority (TNCZMA)** / CRZ Notification 2019 | 1,076 km Tamil Nadu coastline spanning 14 coastal districts. | Detects plots within 500m of high-tide lines (HTL) or tidal estuaries, flagging statutory Coastal Regulation Zone clearances. |
| **Weather & Early Warning** | **India Meteorological Department (IMD)** & Open-Meteo Weather Model | Hourly and 7-day multi-model forecast with cryptographically hashed receipts (SHA-256). | Live temperature, precipitation probability, humidity, wind gust speeds, and seasonal monsoonal alerts. |
| **Administrative & Geocoding** | **Survey of India & OpenStreetMap Nominatim** | All 38 Revenue Districts, taluks, and major metropolitan localities. | Fast dual-tier geocoding resolving places, postal addresses, and GPS coordinates to administrative boundaries. |

---

## 3. Database Schema & Complaint Record Architecture

Complaints in SOLUM are stored in an ACID-compliant SQLite database with Write-Ahead Logging (`WAL` mode) and full schema indexing on `district`, `locality`, and `status`.

### Record Type Classification

To guarantee data integrity and transparency, every issue/complaint record is explicitly tagged:

```json
{
  "id": "SLM-1042",
  "title": "Power line damage",
  "place": "100 Feet Road, Velachery",
  "district": "Chennai",
  "locality": "Velachery",
  "latitude": 12.9780,
  "longitude": 80.2195,
  "status": "In progress",
  "priority": "High",
  "record_type": "demonstration",
  "data_source": "GCC Ward 178 Demonstration Incident Feed"
}
```

1. **`demonstration`**:
   - Seeded reference scenarios to demonstrate system features (e.g. powerline isolation, culvert desilting, road slip stabilization).
   - Tagged with realistic municipal ward references and verified local coordinates.
   - Idempotently seeded; duplicates are strictly prevented.
2. **`user-submitted`**:
   - Submitted live by citizens via the SOLUM Report/Complaint dialog.
   - Automatically tagged with GPS coordinates, auto-detected district/locality, and citizen evidence photos.
   - Stored with `record_type: "user-submitted"` and `data_source: "Citizen complaint (SOLUM Portal)"`.
3. **`real`**:
   - Reserved for synchronized real-time feeds from municipal disaster management grievance redressal systems (e.g., GCC 1913, TNSDMA 1070).

---

## 4. Regional Seed Distribution Across Tamil Nadu

To enable seamless location testing across Tamil Nadu, reference demonstration complaints are seeded across key administrative hubs:

| District | Locality | Ticket ID | Category | Title | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Chennai** | Velachery | `SLM-1042` | Electricity | Power line damage | In progress |
| **Chennai** | Velachery | `SLM-1043` | Drainage | Waterlogging near homes | Open |
| **Chennai** | Taramani | `SLM-1044` | Road | Debris on road | Open |
| **Chennai** | Pallikaranai | `SLM-1045` | Tree | Tree blocking lane | In progress |
| **Chennai** | Velachery | `SLM-1046` | Drainage | Blocked roadside drain | Resolved |
| **Chennai** | Anna Nagar | `SLM-2011` | Drainage | Stormwater culvert siltation | Open |
| **Coimbatore** | Singanallur | `SLM-2021` | Drainage | Singanallur lake weir silt accumulation | In progress |
| **Coimbatore** | RS Puram | `SLM-2022` | Water | Pipeline joint failure on DB Road | Open |
| **Madurai** | Goripalayam | `SLM-2031` | Road | High-mast light circuit failure | In progress |
| **Madurai** | Mattuthavani | `SLM-2032` | Drainage | Bus terminus storm drain blockage | Open |
| **Salem** | Hasthampatti | `SLM-2041` | Road | Culvert apron damage on Yercaud Main Rd | Open |
| **Tiruchirappalli** | Srirangam | `SLM-2051` | Drainage | Cauvery overflow channel desilting | In progress |
| **Nilgiris** | Ooty | `SLM-2061` | Landslide | Embankment soil creep on Ooty-Coonoor Rd | In progress |
| **Kanyakumari** | Kanyakumari | `SLM-2071` | Coastal | Seawall tetrapod displacement | Open |

When a user selects an area without reported issues (e.g., Erode, Dharmapuri, Perambalur), SOLUM displays a genuine empty state:
> *"No reported issues are currently available for this location. You can log a new complaint to alert local authorities."*

---

## 5. Google Maps 3D Platform Architecture

SOLUM utilizes Google Maps JavaScript API with the following mode implementations:
1. **Satellite 3D Perspective**: High-resolution photorealistic aerial imagery tilted at 45° with 3D terrain elevation and geographical surroundings.
2. **True Satellite Basemap**: Orthorectified true satellite imagery directly from Google Earth/Landsat sensors.
3. **2D Civic Plan**: Standard vector roadmap for civil planning, property boundaries, and navigation.
4. **Water Bodies & Catchment Buffers**: Dynamic vector polygon overlays depicting rivers, lakes, reservoirs, and statutory 50m riparian buffer zones sourced from India-WRIS and Tamil Nadu PWD.

The previous dark tinting issue caused by `DEMO_MAP_ID` vector cloud styling has been eliminated, ensuring crisp, natural satellite landscapes across 100% of Tamil Nadu.
