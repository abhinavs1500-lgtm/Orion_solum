# SOLUM integration guide

## Run and modify

Use `python3 server.py`, then http://localhost:8000. The default host is localhost. The site is plain HTML, CSS and JavaScript with a Python standard-library adapter. No framework build is necessary. Edit the root HTML metadata, shared layout in `assets/app.js`, visual rules in `assets/solum.css`, and model geometry in `assets/scene.js`.

## Provider routes

| Local route | Provider | Scope |
| --- | --- | --- |
| `/api/health` | Local | Readiness check |
| `/api/weather?lat=…&lon=…` | `https://api.open-meteo.com/v1/forecast` | Current modeled temperature/code, seven daily highs/lows, maximum rain probability, UV maximum, weather code |
| `/api/geocode?q=…` | `https://geocoding-api.open-meteo.com/v1/search` | Up to five location matches |
| `/api/reverse?lat=…&lon=…` | `https://nominatim.openstreetmap.org/reverse` | User-initiated city/district/state naming |
| `/api/news?region=…&scope=district` | Google News RSS, GDACS RSS | Region-keyword news; scopes: district, state, national |
| Browser satellite request | Esri World Imagery MapServer `export` | Selected-area basemap, not a current damage assessment |

Provider failure returns an explicit unavailable state. No fabricated weather, reports, warnings or hazard timing replaces a failed request. A city search can be used if device location is unavailable. Native geolocation requires a secure context such as HTTPS or localhost and browser permission.

Review provider terms before public or commercial use. The Open-Meteo free API is intended for non-commercial usage subject to its published limits; commercial deployment may need a subscription. Nominatim's public endpoint has a usage policy and is not a high-volume geocoding backend. Use an appropriate identified service, rate limiting and caching for public deployment. Esri imagery access and attribution must follow its current terms. News RSS coverage, availability and usage terms can change.

## Production implementation still required

| Capability | Required next work |
| --- | --- |
| Real 3D location model | Acquire licensed building footprints, elevation and terrain; georeference them; use a GIS/3D engine such as Cesium or Three.js; validate coverage and accuracy. |
| Hazard analysis | Calibrated hydrological / slope / cyclone models, current observations, historical event validation, uncertainty estimates and competent review. An LLM alone must not generate hazard forecasts. |
| Safe routes and shelters | Authoritative road closures, validated hazard layers, open shelter capacity and accessibility; route verification with local responders. |
| Long-term satellite context | Licensed imagery access, geospatial processing, time-series validation, cloud/coverage checks and provenance. None is presently ingested. |
| Officials' accounts | Identity provider, verified roles, server-side authorization, session management and account lifecycle controls. |
| Complaint delivery | Authorized authority API or agreed case-management integration, consent and retention policy, durable storage, malware scanning, moderation, delivery receipts and status reconciliation. |
| AI planning | Grounded workflow tied to real work orders, validated priority criteria and dependencies; human confirmation before dispatch or spending. |
| Land suitability | Authoritative parcel/land-use layers, site-level measurements, geotechnical and structural assessment, applicable rules and professional sign-off. |
| Data integrity | Authenticated ingestion, cryptographic signatures, independently protected audit logs, key management, access controls, backups and tamper detection. Never promise that no attacker can modify data. |
| Generative assistant | Server-side model credentials, source retrieval, grounded responses, explicit refusal to invent forecasts, conversation/data policies and evaluation. |

## Content and trust model

News is third-party coverage. An article about a region does not establish an active hazard at a user's address. The application links out to the full report and official sources. “Breaking” is reserved for fresh publisher-labelled breaking headlines. A missing feed is not an “all clear”.

Weather is a modeled forecast, not a verified street-level flood warning. The retrieval receipt hashes the fetched JSON bytes to support comparison; without a trusted signature and transport/source controls it cannot establish authenticity. Browser-local repair history can be edited and is not a secure audit trail.

## Reference links

- Open-Meteo forecast docs: https://open-meteo.com/en/docs
- Open-Meteo geocoding: https://open-meteo.com/en/docs/geocoding-api
- Open-Meteo terms: https://open-meteo.com/en/terms
- Nominatim policy: https://operations.osmfoundation.org/policies/nominatim/
- GDACS: https://www.gdacs.org/
- IMD Chennai: https://mausam.imd.gov.in/chennai/
- Flood preparedness: https://mausam.imd.gov.in/chennai/mcdata/dos%26donts.pdf
- Greater Chennai Corporation: https://chennaicorporation.gov.in/
- ISRO Bhuvan: https://bhuvan.nrsc.gov.in/
- CMDA: https://www.cmdachennai.gov.in/
