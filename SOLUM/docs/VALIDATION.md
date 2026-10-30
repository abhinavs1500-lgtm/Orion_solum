# Validation record

Prepared 30 October 2026.

## Passed

- JavaScript syntax checks for `assets/app.js` and `assets/scene.js`.
- Python compilation for `server.py`.
- 262 DOM interaction/resource assertions using jsdom: all five pages initialize; unique IDs; label targets; local asset/link existence; news navigation; live and offline weather states; location search; animation chapter controls; map-mode switches; scenario slider; persistent checklist; preparation-guide answers; safe rendering of user text; issue filters; complaint submission; local officials updates and resource allocations; report generation and print action.
- 10 Python server tests: health, unknown endpoints, coordinate validation, invalid regions, weather adapter and digest, unavailable-provider behavior, article freshness, safe source URLs, explicit breaking-label rules, caching and geocoding.
- Live Open-Meteo adapter check: HTTP 200, seven forecast days and a retrieval digest.
- Live Chennai news adapter check: eight recent reports from six publishers; no provider warnings at test time.
- Archive integrity and relative-path checks during packaging.

## Not verified in this environment

The managed browser-preview service was unavailable. No rendered desktop/mobile screenshots or real-browser end-to-end visual checks were possible. DOM tests mocked canvas drawing and therefore do not verify visual rendering, touch behavior, layout, GPU performance or real device location permission. A visual check on your target devices is still needed.

Live checks establish reachability at the time of testing, not provider uptime or public-safety accuracy. Native device geolocation, satellite-image rendering, local media previews and the operating-system print dialog need target-browser verification. The animation is a canvas illustration, not a calibrated GIS simulation or an exported video file.

## Review after starting

1. Check Home at desktop and phone widths; confirm fonts, headline wrapping and all seven weather columns.
2. Allow or decline location permission; confirm a clear result and that city search still works.
3. Play/pause each animation chapter, rotate the model and switch all map modes.
4. Turn off the internet and confirm weather/news display unavailable/reference states.
5. Submit a sample complaint with a small image/video; review its local record.
6. Enter the officials demo, publish a repair update and verify it on Resolve in the same browser.
7. Generate a land checklist and inspect Print / Save PDF output.

See the README for data limitations. No tests establish real hazard forecasting, verified routes, engineering suitability, government delivery, authentication or tamper-proof storage; those capabilities are intentionally not claimed.
