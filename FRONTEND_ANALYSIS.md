# SOLUM — Comprehensive Frontend Analysis Report

**Project:** SOLUM — One view. Every layer. A safer tomorrow.  
**Analysis Date:** October 2026  
**Auditor:** Antigravity Full-Stack & Solutions Architecture  
**Document Target:** `FRONTEND_ANALYSIS.md`  

---

## 1. Executive Summary

SOLUM is an interactive, multi-hazard land intelligence and civic recovery decision-support application. Originally conceived as *TerraShield AI* and styled on a modernized *Hopewell* clean UI/UX template, SOLUM bridges the gap between pre-disaster household preparation, post-disaster civic infrastructure recovery, and pre-construction land due diligence.

The frontend is implemented using vanilla modern JavaScript (ES6+), custom CSS design tokens extending Bootstrap 5, code-native SVG assets, local OFL web fonts (Poppins & Nunito Sans), and an HTML5 canvas 2.5D isometric geometry engine (`SolumScene`). 

Currently, the application relies on:
1. A minimal standard-library Python HTTP server (`SOLUM/server.py`) serving static files and read-only upstream proxy adapters (Open-Meteo for weather/geocoding, Nominatim for reverse geocoding, Google News RSS and GDACS for hazard news).
2. Browser `localStorage` (`solum:*` keys) for storing complaints, repair status updates, officials' audit logs, and household checklists.
3. Hardcoded rule-based simulations for chatbot responses, recovery prioritizations, and land assessment checklists.
4. An illustrative canvas model (`assets/scene.js`) and static ESRI World Imagery raster export for map visualization.

This report details the architectural breakdown, inventory of existing components and features, missing backend services, required API endpoints, technical gaps, and the step-by-step roadmap for full FastAPI backend implementation and Photorealistic Google Maps 3D integration without altering the teammate's frontend styling and animations.

---

## 2. Existing Frontend Architecture

### 2.1 File & Directory Structure

```text
SOLUM/
├── index.html                   # Home page mount (data-page="index")
├── prepare.html                 # Prepare page mount (data-page="prepare")
├── resolve.html                 # Resolve page mount (data-page="resolve")
├── officials.html               # Officials workspace mount (data-page="officials")
├── report.html                  # Land due-diligence report mount (data-page="report")
├── server.py                    # Legacy minimal Python HTTP server (SimpleHTTPRequestHandler)
├── package.json                 # Project descriptor and npm run scripts (no npm dependencies)
├── start-windows.bat            # Windows launcher script
├── start-mac.command            # macOS launcher script
├── start-linux.sh               # Linux launcher script
├── README.md                    # Project documentation and disclosure
├── assets/
│   ├── app.js                   # Core application logic, DOM rendering, handlers & state
│   ├── scene.js                 # 2.5D isometric canvas geometry renderer & animation loop
│   ├── solum.css                # SOLUM custom layouts, cards, dialogs, responsive breakpoints
│   ├── style.css                # Hopewell design tokens, typography, and base styles
│   ├── bootstrap.min.css        # Base Bootstrap 5 framework styles
│   ├── bootstrap.bundle.min.js  # Bootstrap JavaScript bundle
│   ├── fonts.css                # Local font-face declarations
│   ├── fonts/                   # Poppins and Nunito Sans TTF fonts & OFL licenses
│   ├── city.svg                 # Code-native vector city illustration
│   ├── favicon.svg              # App icon
│   └── *-illustration.svg       # Vector illustrations for Prepare, Resolve, Report
└── docs/
    ├── FEATURES-AND-INTEGRATIONS.md  # Upstream integration guides and limitations
    ├── VALIDATION.md                 # Test matrix and verified assertions
    └── TerraShieldAI-reference.pdf    # Concept reference deck
```

### 2.2 Framework, Libraries, & Dependencies

- **Framework:** Vanilla JavaScript (No React, Vue, or Angular). Mounts dynamic HTML templates into `<div id="app"></div>` based on `<body data-page="...">`.
- **CSS Architecture:** 
  - `bootstrap.min.css`: Responsive grid, utilities.
  - `style.css`: Primary theme tokens (`--clr-primary`, `--clr-secondary`, `--font-display`, `--font-body`).
  - `solum.css`: Scoped CSS variables (`--line: #e1e9e4`, `--ink: #10291e`, `--muted: #64766b`, `--mint: #edf8f0`, `--paper: #f8faf9`), glassmorphism overlays, custom button styles (`.btn`, `.btn-soft`, `.btn-ghost`), responsive media queries (`@media (max-width: 1000px)`, `@media (max-width: 720px)`), and print stylesheet.
- **Typography:** Poppins (700, 600) for display/headings and Nunito Sans (400, 600, 700, 800) for body, fully bundled offline.
- **Icons:** SVG path strings rendered via helper `icon(name)` inside `assets/app.js` (no third-party icon font dependency).

### 2.3 Routing & Navigation

- Each of the 5 HTML entry points (`index.html`, `prepare.html`, `resolve.html`, `officials.html`, `report.html`) defines a `data-page` attribute on `<body>`.
- `assets/app.js` evaluates `document.body.dataset.page` and dynamically renders:
  `document.getElementById('app').innerHTML = nav() + pageComponent() + footer() + dialogs();`
- Top navigation bar provides direct links between `Prepare`, `Resolve`, and `Report`.
- On `resolve.html` and `officials.html`, the top nav action switches to `Officials access` (`officials.html`). On other pages, it shows the active location selector pill (`[pin] <City Name>`).

### 2.4 State Management & Data Flow

- **Global In-Memory State:**
  - `locationData`: Object holding `{ name, district, state, country, lat, lon, mode }` (defaults to Chennai: `13.0827, 80.2707`).
  - `issues`: Array of repair issue objects (seeded with `SLM-1042` to `SLM-1046`).
  - `selectedIssue`: Active issue identifier in Resolve view (defaults to `'SLM-1042'`).
  - `newsScope`: `'district' | 'state' | 'national'`.
  - `newsItems`: Array of fetched or fallback news objects.
  - `storyScene` / `mapScene`: Instances of `SolumScene` canvas renderer.
- **Persistence (`store` wrapper):**
  - Uses `localStorage.getItem('solum:' + key)` and `localStorage.setItem('solum:' + key, ...)`.
  - Stored keys: `solum:location`, `solum:issues`, `solum:checklist`, `solum:audit`.
  - Listens to `window.addEventListener('storage', ...)` for cross-tab synchronization of issues.

---

## 3. Detailed Frontend Feature Inventory

| Page | Feature Component | Description | Current Input | Current Output | Current State | Backend Needed? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Global** | Location Picker Modal (`#location-dialog`) | Allows user to choose location via browser GPS or city text search | GPS coordinates or search query string (`q`) | Selected city, district, state, coordinates | Semi-functional (calls Open-Meteo & Nominatim via `/api/geocode`, `/api/reverse`) | **Yes** — robust geocoding, validation, caching & coordinate boundary checks |
| **Global** | Sources & Transparency Modal (`#sources-dialog`) | Displays data source attributions, live receipt digest, and unverified data disclosures | None (click trigger) | Source links and JSON SHA-256 retrieval receipt | Fully functional (client-side modal) | **Yes** — receipt verification & provenance auditing |
| **Index** | Hazard News Carousel (`.news-panel`) | Shows latest regional hazard/disaster articles with scope filter | Scope: `district`, `state`, `national`; region query | Title, publisher, URL, timestamp, `BREAKING` vs `LATEST` badge | Functional via `/api/news` proxying Google News & GDACS RSS | **Yes** — resilient RSS/news ingestion, deduplication, NLP disaster classification |
| **Index** | 7-Day Weather Forecast (`.weather-box`) | Displays weekly modeled temperature, precipitation probability, UV index, weather symbols | Latitude, Longitude | 7-day forecast cards + current weather model + SHA-256 hash | Functional via `/api/weather` proxying Open-Meteo | **Yes** — weather persistence, anomaly detection, threshold risk alerts |
| **Index** | "City Stories" 3D Canvas (`#story-canvas`) | 2.5D isometric animated demonstration of flood, landslide, and cyclone progression | Chapter buttons (`flood`, `landslide`, `cyclone`), play/pause | Canvas animated projection with buildings, trees, water, and debris | Fully functional custom 2.5D canvas simulation | **No** (preserve existing canvas engine as illustrative storytelling) |
| **Prepare** | Scenario Brief Metrics (`.analysis-summary`) | Displays scenario guidance cards (Scenario type, Arrival time, Route safety) | Location coordinates | 3 summary cards with cautionary disclaimers | Hardcoded static HTML | **Yes** — dynamic risk evaluation based on geospatial location |
| **Prepare** | Interactive Map Panel (`.map-panel`) | Interactive canvas showing 3D, 2D, satellite raster, and water corridor modes | Mode buttons, zoom buttons, drag/rotate, scenario timeline slider (0–24h) | Rendered isometric view or ESRI imagery raster | Partially simulated (canvas geometry is procedural; satellite is ESRI MapServer REST export) | **CRITICAL: YES** — Integrate interactive Google Maps 3D environment with camera navigation, 3D building/terrain rendering, and markers |
| **Prepare** | Preparation Checklist (`.action-card`) | Categorized checklist for household emergency readiness | User checkbox clicks | Strikethrough UI + saved to `localStorage` | Functional (browser-local only) | **Yes** — user profile sync, personalized checklist generation based on local risk |
| **Prepare** | "Ask SOLUM" Guide (`.chat-shell`) | Q&A input answering questions about emergency bags, routes, flood timing, data sources | User query string in text input | Chat bubble conversation with source links | Simulated (simple hardcoded regex keyword matching in `askGuide()`) | **Yes** — grounded AI conversational service with safety guardrails and regional disaster guidelines |
| **Resolve** | Resolve Stats Metrics (`#resolve-stats`) | Summary counts for Total, In progress, Resolved, and Awaiting next step | `issues` array in memory/localStorage | 4 numerical metric cards | Functional over client-side array | **Yes** — real-time aggregated metrics from database |
| **Resolve** | Issue List & Filter (`#issue-list`, `#issue-filter`) | Displays list of reported infrastructure damages with priority tags and categories | Filter dropdown (`all`, `open`, `Resolved`, `Electricity`, `Drainage`, `Roads`) | Filtered list of issue cards with chevron navigation | Functional over client-side array | **Yes** — persistent database querying with filtering and sorting |
| **Resolve** | Issue Detail Pane (`#issue-detail`) | Displays progress bar, responsible team, work hours, crew count, milestone steps, risk warning | Selected issue ID | Detailed card with step progress timeline and evidence filenames | Functional over client-side array | **Yes** — persistent issue detail, comments, history tracking |
| **Resolve** | Raise a Complaint Modal (`#complaint-dialog`) | Allows citizens to report issues with category, landmark, description, and photo/video attachments | Form inputs + optional media files (up to 3 files, ≤10MB) | Local preview, assigns `SLM-XXXXXXX` ID, adds to list | Simulated (media is previewed via blob URL; only filenames stored; data lost on storage reset) | **Yes** — multi-part file upload, durable media storage, automated triage, persistent database storage |
| **Officials** | Demo Role Login (`#official-login`) | Role selection modal (District coordination, Rescue team, Infrastructure lead) | Role dropdown selection | Unlocks official workspace view | Simulated (client-side toggle, no actual authentication) | **Yes** — session/JWT authentication, role-based access control (RBAC) |
| **Officials** | Suggested Repair Priorities (`#priority-list`) | Ranked order of open repairs based on life safety and dependencies | Open issues in state | Ranked list with priority badges and crew allocations | Rule-based client-side sorting | **Yes** — algorithm-driven or AI-assisted resource dispatch optimization |
| **Officials** | Budget & Crew Allocation (`#budget-summary`) | Real-time budget progress bar, unallocated funds / funding gap, crew capacity check | Input fields for Available Funds and Available Crew | Calculated cost vs funds meter, shortfall notices | Functional over client-side inputs | **Yes** — project budget tracking and expenditure forecasting |
| **Officials** | Progress Publisher (`#publish-form`) | Updates issue status, % progress, crew, cost, hours, team owner, and public note | Form inputs | Updates issue in array, appends to audit log, updates Resolve view | Functional (browser-local only) | **Yes** — persistent updates, audit logging, notification dispatch |
| **Officials** | JSON Resource Plan Export (`#export-plan`) | Downloads complete recovery plan as JSON file | Current state | Browser file download `SOLUM-resource-plan.json` | Fully functional in browser | **Yes** — server-generated structured report (JSON/PDF/CSV) |
| **Report** | Land Assessment Form (`#land-form`) | Form collecting site address, proposed use, plot area (m²), latitude, longitude | Text, dropdown, numeric inputs | Triggers report generation | Functional (client-side submit event) | **Yes** — coordinate validation and backend spatial analysis pipeline |
| **Report** | Due Diligence Matrix (`#report-result`) | Evaluation matrix covering Flood risk, Water bodies, Soil/geotechnical, Terrain/slope, Zoning, Environmental constraints | Form submission data | Styled table with status badges (`amber`), planning notes, next steps, source links | Simulated (hardcoded static rows, regardless of coordinates entered) | **CRITICAL: YES** — Real GIS/geospatial assessment (Shapely/GeoPandas) querying real elevation, water body proximity, and flood risk |
| **Report** | Print / PDF Export (`#print-report`) | Formats due-diligence report for printing or PDF saving | Click event | `window.print()` with clean print stylesheet | Fully functional | **Yes** — optional server-side PDF generation or receipt signature |

---

## 4. Missing Backend Functionality & Gaps

1. **No True Persistent Database:**
   - Issues, complaints, and official updates live solely in `localStorage`. They do not persist across devices, users, or browser cache resets. A persistent relational store (SQLite with clean PostgreSQL migration readiness) is required.

2. **No Real Land Intelligence / Geospatial Processing:**
   - In `report.html`, entering coordinates (e.g. `12.9815, 80.2180`) produces the identical boilerplate checklist regardless of whether the site is in a flood basin, steep slope, or desert.
   - A real Python geospatial module (utilizing NumPy, Pandas, and Shapely) is needed to calculate elevation, slope risk, distance to nearest water body, drainage catchment exposure, and tailored zoning constraints.

3. **Placeholder Chatbot Engine:**
   - `askGuide()` in `app.js` uses simple regex tests (`/time|when|hour/`, `/route|shelter/`, `/pack|food/`). It cannot answer contextual questions, synthesize data about the selected location, or provide structured explanations. An intelligent, grounded AI backend endpoint is needed.

4. **No Real Complaint & Media Ingestion:**
   - Files uploaded to the complaint modal are merely read as blob URLs for instant preview; no files are saved or processed on a server. A file upload pipeline with MIME-type validation and local/cloud storage is required.

5. **Illustrative Map Instead of Real Google Maps 3D:**
   - In `prepare.html`, the map is an isometric canvas box grid depicting an arbitrary Chennai neighborhood (`assets/scene.js`), plus an ESRI static tile export.
   - Requirement: Integrate Google Maps 3D JavaScript API (`<gmp-map-3d>`) with camera navigation, altitude, heading, tilt, building geometry, 3D markers, and location synchronization.

6. **Missing Multi-User Synchronization:**
   - When an official publishes an update in `officials.html`, only that specific browser session sees it. Citizens accessing `resolve.html` on another device see default seeded issues.

---

## 5. Required Backend API Specification

The FastAPI backend must provide the following modular REST endpoints:

### 5.1 System & Location (`/api`)
- `GET /api/health` — Service readiness, database status, API key verification.
- `GET /api/geocode?q={term}` — City and locality geocoding with caching.
- `GET /api/reverse?lat={lat}&lon={lon}` — Reverse geocoding for device coordinates.
- `GET /api/weather?lat={lat}&lon={lon}` — 7-day weather forecast, UV index, precipitation probability, and SHA-256 retrieval digest.
- `GET /api/news?region={region}&scope={scope}` — Scoped disaster and climate news with freshness filtering and publisher attribution.

### 5.2 Land Assessment & Geospatial Intelligence (`/api/land`)
- `POST /api/land/assess` — Accepts `{ address, proposed_use, area_sqm, latitude, longitude }`. Computes real terrain slope, elevation profile, distance to surface water, historical flood exposure score, and tailored due-diligence matrix.
- `GET /api/land/report/{report_id}` — Retrieves historical assessment record.

### 5.3 Civic Issues & Complaints (`/api/issues`)
- `GET /api/issues?status={status}&category={category}` — Returns filtered list of civic infrastructure repairs.
- `GET /api/issues/stats` — Returns aggregate counters (`total`, `in_progress`, `resolved`, `awaiting`).
- `GET /api/issues/{id}` — Returns single issue details, milestones, crew, and audit trail.
- `POST /api/issues` — Multi-part endpoint accepting subject, category, place, description, coordinates, and optional evidence files (images/videos). Stores files securely, assigns ticket ID, and creates DB record.

### 5.4 Officials & Planning Workspace (`/api/officials`)
- `GET /api/officials/priorities` — Returns open issues dynamically ranked by life-safety impact, dependency chains, and crew feasibility.
- `POST /api/officials/updates` — Records official status updates (`status`, `progress`, `crew`, `cost`, `hours`, `owner`, `note`).
- `GET /api/officials/audit` — Retrieves chronological audit log of published actions.
- `GET /api/officials/plan/export` — Generates structured resource allocation plan.

### 5.5 AI Decision Support & Chatbot (`/api/chat`)
- `POST /api/chat` — Accepts `{ message, location: { name, lat, lon }, context }`. Returns grounded, source-linked safety and land guidance via Fast/Accurate AI inference with strict disaster safety guardrails.

### 5.6 Google Maps 3D Support (`/api/maps`)
- `GET /api/maps/config` — Returns client configuration (Map ID, library version, initial coordinates) without exposing backend secrets.
- `POST /api/maps/location-context` — Accepts coordinates; returns 3D overlay layers, water corridors, elevation markers, and risk hotspots for rendering directly on the 3D map.

---

## 6. Google Maps 3D Integration Architecture

### 6.1 Technology Choice & Strategy
- **API:** Google Maps JavaScript API with Photorealistic 3D Maps (`v=alpha`, `maps3d` library).
- **Web Component:** `<gmp-map-3d>` custom element.
- **Attributes & Features:**
  - `center`: `lat, lng, altitude`
  - `tilt`: Smoothly pitch camera between 0° and 67.5°
  - `heading`: 360° rotational camera bearing
  - `range`: Distance from target (camera altitude / zoom scale)
  - Interactive camera control: `flyCameraTo()` with smooth interpolation for animated location transitions.
  - 3D Elements: `<gmp-marker-3d>` for damage hotspots and landmark identification; `<gmp-polygon-3d>` or `<gmp-polyline-3d>` for water corridors and evacuation bounds where supported.

### 6.2 UI Integration in `prepare.html`
- Replace or augment the static map canvas inside `.map-panel` seamlessly:
  - Add a dedicated `<div id="gmp-3d-container"></div>` inside `.map-panel`.
  - Maintain the existing `.map-top` header, `.map-modes` switcher buttons (`3D view`, `2D view`, `Satellite`, `Water bodies`), and `.map-zoom` buttons.
  - When the user selects **3D view**, display the live Google Maps 3D environment!
  - When the user clicks **Satellite**, render Google Maps Satellite/Hybrid basemap.
  - When the user clicks **Water bodies**, overlay hydrological polygons/water features.
  - When the user changes location (via city search or "Use my current location"), programmatically call `flyCameraTo({ endCamera: { center: { lat, lng, altitude: 400 }, tilt: 60, heading: 30, range: 1200 }, durationMillis: 2500 })`.
  - Clicking on the 3D map captures coordinates, syncs with the land assessment tools, and updates the local preparation brief.

### 6.3 Graceful Degradation & Fallback
- For environments where WebGL2/Hardware acceleration is restricted, fallback gracefully to the 2.5D Canvas engine (`SolumScene`) or 2D Google Maps without breaking the page or throwing unhandled exceptions.

---

## 7. Preservation of Design & Performance Principles

In strict adherence to the project rules:
1. **Zero Frontend Rebuild:** The existing DOM structure, HTML layouts, button positions, cards, and modal dialogs are completely preserved.
2. **Design Tokens & Theme:** All colors (`#0f7a37`, `#16a34a`, `#edf8f0`, `#f8faf9`), typography (Poppins, Nunito Sans), card borders (`#e1e9e4`), and shadows are untouched.
3. **No Disruptive Overhauls:** The home page layout, "City Stories" animation canvas, and vector illustrations remain in place.
4. **Performance:** Asynchronous script loading for Google Maps 3D, efficient event listener cleanup, responsive layout preservation, and low-latency API response caching (10-minute in-memory + SQLite).

---

## 8. Recommended Implementation Order

1. **Phase 1 (Completed):** Complete frontend audit, code analysis, and generation of `FRONTEND_ANALYSIS.md`.
2. **Phase 2:** Backend Architecture Design (`BACKEND_ARCHITECTURE.md`) defining models, database schema, and services.
3. **Phase 3:** Backend Foundation — Implement FastAPI app (`main.py`, models, SQLite database, routers, CORS, and error handlers).
4. **Phase 4:** Google Maps 3D Integration — Embed `<gmp-map-3d>` with authorized API key handling, smooth camera transitions, markers, and controls.
5. **Phase 5:** Feature-by-Feature API Integration — Connect location geocoding, persistent complaints & issue tracking, officials workspace, and AI guide.
6. **Phase 6:** Geospatial Land Due-Diligence Pipeline — Implement real coordinate-driven terrain and flood risk analysis.
7. **Phase 7:** End-to-End Testing & Verification across all 5 pages.
8. **Phase 8:** Final Polish, Documentation (`README.md`, `.env.example`, deployment guides).

---
*Report prepared and submitted for review prior to commencing Phase 2 backend architecture implementation.*
