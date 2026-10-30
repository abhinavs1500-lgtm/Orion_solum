# SOLUM — Backend Architecture & System Design

**Project:** SOLUM — One view. Every layer. A safer tomorrow.  
**Document:** `BACKEND_ARCHITECTURE.md`  
**Version:** 1.0.0 (Production-Ready Architecture)  

---

## 1. Architectural Overview

The SOLUM backend is designed as a high-performance, modular Python **FastAPI** service serving both dynamic REST APIs and the static frontend assets. It bridges client-side civic actions (household preparation, neighborhood infrastructure repairs, land assessment) with server-side persistent storage, geospatial analysis, live environmental data ingestion, and interactive Google Maps 3D rendering.

```
                      ┌───────────────────────────────────────────────┐
                      │              SOLUM Web Frontend               │
                      │  (HTML5, Vanilla ES6+, CSS Tokens, Web Comps) │
                      └───────────────────────┬───────────────────────┘
                                              │ REST / JSON / HTTP Multipart
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FastAPI Application                                       │
│                                                                                             │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────────────────────┐  │
│  │     System Router     │  │     Issues Router     │  │       Officials Router          │  │
│  │   • /api/health       │  │   • GET  /api/issues  │  │   • GET  /api/officials/priorities│
│  │   • /api/geocode      │  │   • POST /api/issues  │  │   • POST /api/officials/updates │  │
│  │   • /api/reverse      │  │   • GET  /api/stats   │  │   • GET  /api/officials/audit   │  │
│  │   • /api/weather      │  │   • Media Uploader    │  │   • GET  /api/officials/export  │  │
│  │   • /api/news         │  └───────────────────────┘  └─────────────────────────────────┘  │
│  └───────────────────────┘                                                                  │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────────────────────┐  │
│  │  Land & Geo Router    │  │   AI Chat Router      │  │        Maps 3D Router           │  │
│  │   • POST /api/land/   │  │   • POST /api/chat    │  │   • GET  /api/maps/config       │  │
│  │          assess       │  │   • Grounded Advisor  │  │   • POST /api/maps/context      │  │
│  │   • GET  /api/land/   │  │   • IMD/NDMA Guidelines│ │   • 3D Coordinates & Bounds     │  │
│  │          reports/{id} │  └───────────────────────┘  └─────────────────────────────────┘  │
│  └───────────────────────┘                                                                  │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────┐
                        ▼                                             ▼
┌─────────────────────────────────────────────┐  ┌────────────────────────────────────────────┐
│         Data & Persistence Services         │  │             Upstream Providers             │
│  • SQLite Engine (`solum.db`)               │  │  • Google Maps Platform (3D & Places)      │
│  • Pydantic V2 Schemas & Data Validation    │  │  • Open-Meteo (Forecasts & Geocoding)      │
│  • Shapely / GeoPandas Spatial Analysis     │  │  • OpenStreetMap Nominatim (Reverse Geo)   │
│  • In-Memory TTL Cache (10m TTL)            │  │  • Google News RSS & GDACS (Disaster News) │
│  • Uploads Folder (`uploads/`)              │  │  • National Disaster Protocols (IMD/NDMA)  │
└─────────────────────────────────────────────┘  └────────────────────────────────────────────┘
```

---

## 2. Technology Stack

- **Backend Web Framework:** FastAPI (v0.141+) running on Starlette / AnyIO for asynchronous I/O and low latency.
- **ASGI Server:** Uvicorn (v0.52+) with auto-reloading for development and multi-worker capacity for production.
- **Data Validation & Serialization:** Pydantic V2 for schema contracts and strict runtime validation.
- **Database & Storage:** SQLite (`sqlite3` / SQLAlchemy-ready schema) with foreign keys, WAL journaling for concurrency, and an explicit migration path to PostgreSQL (`psycopg2` / `asyncpg`).
- **Geospatial Processing:** Shapely (v2.2+) and NumPy for point-in-polygon analysis, hydrological buffer calculation, slope gradient estimation, and elevation hazard profiling.
- **HTTP Client:** `httpx` (v0.28+) with async connection pooling, configurable timeouts, and retry policies.
- **Maps & 3D Visualization:** Google Maps JavaScript API Photorealistic 3D Maps (`v=alpha`, `<gmp-map-3d>` web component).

---

## 3. Database Schema Design

The SQLite database (`SOLUM/solum.db`) implements durable relational storage for all civic issues, citizen complaint submissions, uploaded media references, officials' change audits, and land assessments.

```sql
-- Issues and Repairs Table
CREATE TABLE IF NOT EXISTS issues (
    id TEXT PRIMARY KEY,                       -- e.g. 'SLM-1042'
    title TEXT NOT NULL,
    place TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    type TEXT NOT NULL,                        -- 'Electricity', 'Drainage', 'Roads', 'Telecom', 'Other'
    icon TEXT NOT NULL,                        -- 'bolt', 'water', 'tree', 'network', 'tool'
    priority TEXT NOT NULL,                    -- 'Critical', 'High', 'Medium', 'Unassessed'
    status TEXT NOT NULL,                      -- 'Assessment', 'Assigned', 'In progress', 'Resolved'
    progress INTEGER NOT NULL DEFAULT 0,       -- 0 to 100
    crew INTEGER NOT NULL DEFAULT 0,
    cost INTEGER NOT NULL DEFAULT 0,           -- Estimated INR cost
    hours INTEGER NOT NULL DEFAULT 0,          -- Work hours
    owner TEXT NOT NULL,                       -- Responsible team
    reason TEXT NOT NULL,                      -- Priority rationale
    dependency TEXT NOT NULL,                  -- Prerequisites / blockers
    latest_update TEXT NOT NULL,               -- Citizen-facing progress note
    steps_json TEXT NOT NULL,                  -- JSON array of milestone steps
    risk_advisory TEXT NOT NULL,               -- Safety advisory for residents
    evidence_json TEXT,                        -- JSON array of uploaded file paths/names
    is_local_submission BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Officials Action Audit Log
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT NOT NULL,
    actor_role TEXT,                           -- e.g. 'District coordination officer'
    crew_allocated INTEGER,
    cost_allocated INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(issue_id) REFERENCES issues(id)
);

-- Land Assessment Reports
CREATE TABLE IF NOT EXISTS land_reports (
    id TEXT PRIMARY KEY,                       -- e.g. 'LND-202610-XXXX'
    site_address TEXT NOT NULL,
    proposed_use TEXT NOT NULL,                -- 'Individual home', 'Apartment building', etc.
    plot_area_sqm REAL NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    elevation_m REAL,
    slope_percent REAL,
    water_distance_m REAL,
    flood_risk_level TEXT NOT NULL,            -- 'Low', 'Moderate', 'High', 'Severe'
    matrix_json TEXT NOT NULL,                 -- Detailed evaluation matrix
    recommendations_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Uploaded Evidence Media
CREATE TABLE IF NOT EXISTS evidence_files (
    id TEXT PRIMARY KEY,
    issue_id TEXT,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(issue_id) REFERENCES issues(id)
);
```

---

## 4. Detailed API Specifications

### 4.1 System & Environmental Endpoints

- **`GET /api/health`**  
  Returns server status, database connection, uptime, and configured features.
- **`GET /api/geocode?q={term}`**  
  Resolves geographic entities using Open-Meteo Geocoding API with 1-hour cache.
- **`GET /api/reverse?lat={lat}&lon={lon}`**  
  Resolves coordinates to structured address using Nominatim with 24-hour cache.
- **`GET /api/weather?lat={lat}&lon={lon}`**  
  Fetches 7-day weather model, daily highs/lows, rain probability, UV index, and computes a cryptographic SHA-256 receipt for data provenance.
- **`GET /api/news?region={region}&scope={district|state|national}`**  
  Retrieves disaster and climate articles from Google News RSS and GDACS, filters to the last 7 days, assigns `BREAKING` vs `LATEST COVERAGE` badges, and includes publisher attribution links.

### 4.2 Civic Issues & Complaints (`/api/issues`)

- **`GET /api/issues`**  
  Query parameters: `status`, `category`, `search`. Returns list of active issues with progress, crew allocations, and status tags.
- **`GET /api/issues/stats`**  
  Returns aggregate counts: `{"total": 5, "in_progress": 2, "resolved": 1, "awaiting": 2}`.
- **`GET /api/issues/{id}`**  
  Returns single issue with full milestones, audit history, and evidence file URLs.
- **`POST /api/issues`**  
  Multi-part form endpoint accepting:
  - `subject`: string (max 100)
  - `category`: 'Roads' | 'Electricity' | 'Drainage' | 'Telecom' | 'Other'
  - `place`: string (location landmark)
  - `description`: string (min 15 chars)
  - `latitude`, `longitude`: optional floats
  - `files`: optional upload of up to 3 image/video files (max 10MB each)
  Saves files securely to `uploads/`, generates ticket `SLM-XXXXXXX`, inserts into database, and returns the persisted record.

### 4.3 Officials Coordination (`/api/officials`)

- **`GET /api/officials/priorities`**  
  Dynamic priority ranking algorithm sorting issues: Life safety (`Electricity` & unisolated lines) → Critical drainage → Access corridors (`Roads`) → General restoration.
- **`POST /api/officials/updates`**  
  Payload: `{ issue_id, status, progress, crew, cost, hours, owner, note, actor_role }`.  
  Updates the issue, enforces status consistency (e.g. `progress=100` only on `Resolved`), logs to `audit_logs`, and notifies connected clients.
- **`GET /api/officials/audit`**  
  Returns the last 20 official actions with timestamps, notes, and roles.
- **`GET /api/officials/plan/export`**  
  Generates and downloads a complete JSON resource recovery plan.

### 4.4 Geospatial Land Assessment (`/api/land`)

- **`POST /api/land/assess`**  
  Payload: `{ address, proposed_use, area_sqm, latitude, longitude }`.  
  **Geospatial Computation:**
  1. Coordinate validation (-90 to 90, -180 to 180).
  2. Elevation & terrain slope estimation using regional digital elevation model (DEM) approximation.
  3. Distance calculation to nearest known water body/waterway using Shapely spatial geometry.
  4. Flood exposure categorization based on elevation, catchment buffer, and precipitation history.
  5. Use-specific compliance check (Individual home, Apartment, Commercial, Community).
  6. Returns structured report object with matrix rows (status: `clear`, `amber`, `red`), planning considerations, and next steps.

### 4.5 Grounded AI Preparedness Advisor (`/api/chat`)

- **`POST /api/chat`**  
  Payload: `{ message, location: { name, lat, lon } }`.  
  Returns grounded, helpful preparedness guidance based on official disaster checklists (IMD Chennai Flood Dos and Don'ts, NDMA protocols).  
  Explicitly rejects hallucinatory disaster arrival countdowns or unverified safe routes; provides structured checklists for emergency bags, power line safety, and family contact plans.

### 4.6 Google Maps 3D Integration (`/api/maps`)

- **`GET /api/maps/config`**  
  Returns safe client initialization configuration: authorized Google Maps JS API script URL, initial coordinates, tilt, range, and enabled 3D layers.
- **`POST /api/maps/location-context`**  
  Accepts `{ latitude, longitude }` and returns contextual 3D overlay data: active nearby reported issues, water corridor coordinates, and terrain risk polygons.

---

## 5. Google Maps 3D Implementation Strategy

1. **Web Component Integration:**
   - In `SOLUM/prepare.html`, `<gmp-map-3d>` is embedded directly inside `.map-panel`.
   - Script loader loads Google Maps JavaScript API with `v=alpha&libraries=maps3d,places,marker` using the provided key.
2. **Camera Navigation & Synchronization:**
   - When user searches for a city (e.g. Chennai, Bangalore, Mumbai) or uses device location, the map invokes:
     ```javascript
     map3d.flyCameraTo({
       endCamera: {
         center: { lat: newLat, lng: newLon, altitude: 450 },
         tilt: 60,
         heading: 25,
         range: 1200
       },
       durationMillis: 2000
     });
     ```
3. **Interactive 3D Markers:**
   - Active civic issues (e.g. fallen trees, waterlogging, damaged power lines) are rendered as `<gmp-marker-3d>` elements directly in the 3D space with click listeners opening issue details.
4. **Seamless View Mode Switching:**
   - Preserves teammate's existing tab controls:
     - `3D view`: Activates `<gmp-map-3d>` photorealistic 3D map.
     - `2D view`: Renders 2D Google Roadmap / Terrain view.
     - `Satellite`: Renders Google Photorealistic Satellite / Hybrid view.
     - `Water bodies`: Overlays hydrological catchments.

---

## 6. Directory Layout for Backend Implementation

```
SOLUM/
├── backend/
│   ├── __init__.py
│   ├── config.py             # Environment settings & API keys
│   ├── database.py           # SQLite connection & schema initialization
│   ├── models.py             # Pydantic request/response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── geo_service.py     # Geospatial & land assessment algorithms (Shapely)
│   │   ├── weather_service.py # Open-Meteo caching & SHA-256 receipts
│   │   ├── news_service.py    # RSS parsing & disaster classification
│   │   ├── issues_service.py  # Issue tracking, priority ranking, and audits
│   │   └── chat_service.py    # Grounded preparedness advisory
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── system.py          # /api/health, /api/geocode, /api/weather, /api/news
│   │   ├── issues.py          # /api/issues, /api/issues/stats, upload
│   │   ├── officials.py       # /api/officials/priorities, updates, export
│   │   ├── land.py            # /api/land/assess, reports
│   │   ├── chat.py            # /api/chat
│   │   └── maps.py            # /api/maps/config, /api/maps/location-context
│   └── main.py               # FastAPI entry point, CORS, static file mount
├── uploads/                  # Durable storage for uploaded evidence files
├── solum.db                  # Local SQLite database
├── server.py                 # Unified launcher executing FastAPI via Uvicorn
├── .env                      # Local environment configuration
└── .env.example              # Template documentation for environment variables
```

---

*This architecture guarantees 100% preservation of your teammate's visual frontend, elevates simulated features into fully functional data-driven services, and introduces true Photorealistic Google Maps 3D.*
