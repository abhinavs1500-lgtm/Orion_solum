# SOLUM — One view. Every layer. A safer tomorrow.

SOLUM is an interactive, data-driven multi-hazard land intelligence, civic recovery, and due-diligence decision-support platform. It pairs the Google Maps 3D Platform with high-performance Python FastAPI backend services, SQLite persistence, and Shapely geospatial analytics.

---

## 🌟 Key Capabilities & Features

### 1. Interactive Google Maps 3D Platform (`prepare.html`)
- **Photorealistic 3D Environment:** Renders terrain, photorealistic 3D buildings, and geographic context using the official Google Maps JavaScript API 3D Web Component (`<gmp-map-3d>`).
- **Smooth Camera Navigation:** Automated `flyCameraTo()` transitions with pitch, 360° heading, and zoom altitude whenever a location is selected or searched.
- **Responsive 3D Controls:** Zoom In (`+`), Zoom Out (`−`), 3D Camera Tilt Toggle (`📐`), and View Reset (`↺`).
- **3D Hazard Hotspots & Markers:** Renders active reported civic issues as `<gmp-marker-3d>` elements positioned directly in the 3D space with altitude clearance.
- **Interactive Coordinate Inspection:** Click anywhere on the 3D map to capture latitude/longitude, inspect terrain elevation, and query local drainage catchment exposure.
- **Multi-Mode Visualization:** Switch seamlessly between **3D View**, **2D Schematic Plan**, **Satellite Basemap**, and **Water Corridors**.

### 2. Civic Recovery Board (`resolve.html`)
- **Persistent Issue Tracking:** Real-time infrastructure repair status backed by a persistent SQLite database (`solum.db`).
- **Dynamic Counters:** Live metrics for total reported issues, active repairs in progress, completed resolutions, and pending assessments.
- **Raise a Complaint:** Citizens can submit reports with category, landmark location, detailed description, and multi-file photo/video evidence uploads.
- **Progress Tracking:** Milestones, work hours, assigned response crews, and public safety advisories.

### 3. Officials Coordination Workspace (`officials.html`)
- **Dynamic Repair Prioritization:** Intelligent triage based on life safety (electrical isolation), critical dependencies, road access, and utility restoration.
- **Resource & Budget Management:** Real-time balancing of available funds (₹) and crew capacity against open repair requirements.
- **Audit Logging:** Every published status note, crew adjustment, or state change is permanently logged with timestamps and actor roles.
- **Plan Export:** One-click JSON export (`/api/officials/plan/export`) of the prioritized recovery resource plan.

### 4. Land Due-Diligence Pipeline (`report.html`)
- **Geospatial Terrain Intelligence:** Computes real elevation profile and terrain slope gradient for entered site coordinates.
- **Water Body Proximity (Shapely):** Calculates distance to nearest river basins, canals, or protected wetlands (e.g., Adyar, Cooum, Pallikaranai marsh).
- **Comprehensive 6-Layer Due-Diligence Matrix:** Evaluates Flood & Waterlogging, Water Bodies & Buffers, Soil & Foundation, Terrain & Access, Land Use & Zoning, and Environmental Constraints.
- **Tailored Use Considerations:** Specific guidelines for Individual Homes, Apartments, Commercial Buildings, and Community Facilities.
- **Print / Save PDF:** Clean, professional print stylesheet formatting.

### 5. Grounded AI Preparedness Advisor (`prepare.html`)
- **Authoritative Disaster Guidance:** Source-grounded advice for emergency household supply kits, floodwater safety, electrical hazards, and family communications based on IMD & NDMA guidelines.
- **Strict Guardrails:** Explicit refusal to generate unverified flood arrival countdowns or unverified safe routes.

### 6. Environmental Intelligence & Disaster News (`index.html`)
- **7-Day Meteorological Forecast:** High/low temperatures, precipitation probability, UV index, and weather symbols powered by Open-Meteo.
- **Cryptographic Provenance Receipt:** Verifiable SHA-256 hash computed for every retrieved weather payload.
- **Disaster News Carousel:** Scoped to District, State, or National levels with automated breaking-news badge detection from verified publishers via Google News RSS and GDACS.
- **"City Stories" Animation:** 2.5D isometric animated simulation of Flood, Landslide, and Cyclone progression (`assets/scene.js`).

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13)
- Internet connection (for Google Maps 3D tiles, weather, and news)

### 1. Environment Setup
Create or verify your `.env` file in the project folder:
```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
HOST=127.0.0.1
PORT=8000
ENVIRONMENT=development
DATABASE_URL=sqlite:///./solum.db
```

### 2. Run the Application
You can use the native launcher for your operating system:

| Platform | Command / Launcher |
| :--- | :--- |
| **Windows** | Double-click `start-windows.bat` or run `python server.py` |
| **macOS** | Run `bash start-mac.command` |
| **Linux** | Run `sh start-linux.sh` |
| **Manual** | `python server.py --host 127.0.0.1 --port 8000` |

Visit **`http://localhost:8000`** in any modern web browser (Chrome, Edge, Firefox, Safari).

---

## 📡 REST API Documentation

FastAPI provides interactive Swagger/OpenAPI documentation at:
- **Interactive Swagger UI:** `http://localhost:8000/docs`
- **ReDoc UI:** `http://localhost:8000/redoc`

### Key Endpoints

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **System** | `GET` | `/api/health` | Service health, version, and Maps 3D status |
| **System** | `GET` | `/api/geocode?q={term}` | City and locality geocoding |
| **System** | `GET` | `/api/reverse?lat={lat}&lon={lon}` | Reverse geocoding for GPS coordinates |
| **System** | `GET` | `/api/weather?lat={lat}&lon={lon}` | 7-day weather model with SHA-256 receipt |
| **System** | `GET` | `/api/news?region={region}&scope={scope}` | Scoped disaster news from Google News & GDACS |
| **Maps 3D** | `GET` | `/api/maps/config` | Client 3D configuration & authorized loader |
| **Maps 3D** | `POST` | `/api/maps/location-context` | 3D markers, water corridors & elevation |
| **Issues** | `GET` | `/api/issues` | Filterable list of civic infrastructure repairs |
| **Issues** | `GET` | `/api/issues/stats` | Summary counts of issue statuses |
| **Issues** | `POST` | `/api/issues` | Multi-part complaint submission with file uploads |
| **Officials**| `GET` | `/api/officials/priorities` | Dynamic life-safety and dependency ranking |
| **Officials**| `POST` | `/api/officials/updates` | Publish official repair updates & audit log |
| **Officials**| `GET` | `/api/officials/audit` | Chronological audit trail of published actions |
| **Officials**| `GET` | `/api/officials/plan/export` | Download recovery resource plan JSON |
| **Land** | `POST` | `/api/land/assess` | Shapely geospatial due-diligence report |
| **AI Guide** | `POST` | `/api/chat` | Grounded safety and preparedness Q&A |

---

## 🧪 Testing & Verification

A dedicated verification test suite is included in `test_backend.py`.

Run the automated test suite:
```bash
python test_backend.py
```
This tests all 12 core sub-systems:
1. Health endpoint & configuration check
2. Google Maps 3D config endpoint
3. 3D location context & active markers
4. Live weather forecast & SHA-256 cryptographic digest
5. Geocoding search service
6. Disaster news retrieval & classification
7. Issues listing & stats counters
8. Multi-part complaint creation & SQLite storage
9. Officials priority sorting, updates, audit log & plan export
10. Shapely geospatial land assessment pipeline
11. Grounded AI chat advisor
12. Static serving of all 5 frontend HTML pages

---

## 🚢 Deployment Guidelines

### Production Hosting Architecture
- **Frontend & Static Assets:** Served directly via FastAPI StaticFiles or fronted by a reverse proxy (Nginx, Caddy, Cloudflare).
- **Backend Service:** Deploy FastAPI on any Python container or VM (Google Cloud Run, AWS App Runner, Render, Railway, DigitalOcean App Platform):
  ```bash
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
  ```
- **Google Maps API Key Protection:**
  - In Google Cloud Console, restrict your API key to **HTTP Referrers** matching your production domain (e.g. `https://your-domain.com/*`).
  - Restrict the key's API access to **Maps JavaScript API**, **Places API (New)**, and **Geocoding API**.
- **Database Migration:**
  - The SQLite database (`solum.db`) uses standard SQL schemas. For horizontal scaling or multi-region deployments, switch to managed PostgreSQL by updating `DATABASE_URL=postgresql://user:password@host/solum` in `.env`.

---

## 📄 Attribution & Licenses
- **Design & Themes:** Adapted from the Hopewell theme (ThemeWagon, MIT License) and TerraShield AI concept deck.
- **Maps:** Google Maps Platform (Maps JavaScript API 3D Maps).
- **Weather:** Open-Meteo (CC BY 4.0).
- **Geocoding:** Open-Meteo & OpenStreetMap Nominatim.
- **News:** Google News RSS & GDACS.
- **Fonts:** Poppins & Nunito Sans (SIL Open Font License).

---
*SOLUM is an interactive decision-support platform designed to assist communities and civic teams with evidence-linked preparation, recovery, and land intelligence.*
