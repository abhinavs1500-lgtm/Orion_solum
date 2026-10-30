'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeURL=u=>{try{const v=new URL(u);return ['https:','http:'].includes(v.protocol)?v.href:'#'}catch{return '#'}};
const icons={shield:'M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6Z M8 12l3 3 5-6',pin:'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z M15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0',arrow:'M4 12h16 M14 6l6 6-6 6',layers:'m3 8 9-5 9 5-9 5Z M3 12l9 5 9-5 M3 16l9 5 9-5',cloud:'M6 18a5 5 0 0 1-1-10 7 7 0 0 1 13-1 5.5 5.5 0 0 1 0 11Z',sun:'M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0 M12 1v3 M12 20v3 M1 12h3 M20 12h3 M4 4l2 2 M18 18l2 2 M4 20l2-2 M18 6l2-2',tool:'m14 7 3 3 5-5a7 7 0 0 1-9 9l-7 7a3 3 0 0 1-4-4l7-7a7 7 0 0 1 9-9Z',report:'M6 3h9l4 4v14H6Z M14 3v5h5 M9 12h7 M9 16h7',check:'M5 12l5 5L20 6',alert:'m12 3 10 18H2Z M12 9v5 M12 17v1',bolt:'m13 2-9 12h7l-1 8 10-13h-7Z',water:'M3 7q3-4 6 0t6 0 6 0 M3 12q3-4 6 0t6 0 6 0 M3 17q3-4 6 0t6 0 6 0',tree:'m12 2-7 8h3l-5 7h7v5h4v-5h7l-5-7h3Z',network:'M12 14v7 M8 21h8 M5 11a10 10 0 0 1 14 0 M2 7a15 15 0 0 1 20 0 M9 14a4 4 0 0 1 6 0',home:'m3 11 9-8 9 8 M5 10v11h14V10 M9 21v-8h6v8',search:'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0 M15 15l7 7',clock:'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0 M12 6v6l4 3',lock:'M5 10h14v11H5Z M8 10V6a4 4 0 0 1 8 0v4 M12 14v3',people:'M10 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0 M1 21v-5a6 6 0 0 1 12 0v5 M19 9a3 3 0 1 1-4-5 M16 13a6 6 0 0 1 7 6v2',play:'m8 4 12 8-12 8Z',download:'M12 3v13 M7 11l5 5 5-5 M4 17v4h16v-4',mail:'M3 5h18v14H3Z m0 0 9 8 9-8',close:'m6 6 12 12 M6 18 18 6',info:'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0 M12 11v6 M12 7v1'};
const icon=(name)=>`<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${icons[name]||icons.layers}"/></svg>`;
const store={get(k,f){try{return JSON.parse(localStorage.getItem('solum:'+k))??f}catch{return f}},set(k,v){try{localStorage.setItem('solum:'+k,JSON.stringify(v));return true}catch{toast('Browser storage is unavailable. Changes last for this session only.');return false}}};
const defaults={name:'Chennai',district:'Chennai',state:'Tamil Nadu',country:'India',lat:13.0827,lon:80.2707,mode:'Selected city'};
let locationData=store.get('location',defaults),page=document.body.dataset.page,newsScope='district',newsIndex=0,newsPaused=matchMedia('(prefers-reduced-motion: reduce)').matches,newsItems=[],newsGeneration=0,weatherGeneration=0,storyScene,mapScene,selectedIssue='SLM-1042';
let gmpLoaded=false, googleMap3D=null, googleMap=null, googleMapMarkers=[], googleMap3DMarkers=[], Map3DElementClass=null, Marker3DElementClass=null, map3dSupported=true, isOrbiting=false, currentHeading=20, currentTilt=65, activeMapMode='3d';
let simMeta=null, simHour=0, simPlaying=false, simTimer=null, simCache={}, simGeoJsonFeatures=[], sim3DMarkers=[];
let officialSession=store.get('official_session',null), solumAiOpen=false, chatHistory=[];

function formatLocationDisplay(loc){
  if(!loc)return 'Tamil Nadu';
  if(typeof loc==='string'){
    const parts=loc.split(',').map(s=>s.trim()).filter(Boolean);
    const seen=new Set(),out=[];
    for(const p of parts){
      const clean=p.replace(/\s+District$/i,'').trim();
      const l=clean.toLowerCase();
      if(!seen.has(l)){
        seen.add(l);
        out.push(clean);
      }
    }
    return out.join(', ')||loc;
  }
  const locality=(loc.locality||'').trim();
  const name=(loc.name||'').trim();
  const district=(loc.district||'').replace(/\s+District$/i,'').trim();
  const state=(loc.state||'Tamil Nadu').trim();
  const parts=[],seen=new Set();
  const addPart=p=>{
    if(!p)return;
    const clean=p.replace(/\s+District$/i,'').trim();
    const l=clean.toLowerCase();
    if(!seen.has(l)){
      seen.add(l);
      parts.push(clean);
    }
  };
  if(locality)addPart(locality);
  if(name)addPart(name);
  if(district)addPart(district);
  if(parts.length===1&&state)addPart(state);
  return parts.join(', ')||'Tamil Nadu';
}

function formatShortLocation(loc){
  if(!loc)return 'Tamil Nadu';
  if(typeof loc==='string')return loc.split(',')[0].trim();
  return loc.locality||loc.name||'Tamil Nadu';
}

const issuesSeed=[
{id:'SLM-1042',title:'Power line damage',place:'Velachery Main Road',type:'Electricity',icon:'bolt',priority:'Critical',status:'In progress',progress:45,crew:8,cost:240000,hours:6,owner:'Electricity response team',reason:'Isolate electrical hazards before pumping or road clearance.',dependency:'Isolation clearance before SLM-1043',update:'Isolation completed; replacement pole and cable crew assigned.',steps:['Citizen report received','Electrical isolation confirmed','Replacement work in progress','Inspection and safe restoration'],risk:'Keep clear of fallen wires and flooded electrical equipment.'},
{id:'SLM-1043',title:'Waterlogging near homes',place:'Ram Nagar · Velachery',type:'Drainage',icon:'water',priority:'High',status:'In progress',progress:30,crew:6,cost:180000,hours:8,owner:'Stormwater drainage team',reason:'Restore access to homes after electrical clearance.',dependency:'Depends on SLM-1042 isolation',update:'Pumps staged; electrical clearance is required before entry.',steps:['Site assessed','Pumping team allocated','Pumping and drain clearance','Access inspected'],risk:'Do not walk or drive through floodwater.'},
{id:'SLM-1044',title:'Fallen tree blocking access',place:'Taramani Link Road',type:'Roads',icon:'tree',priority:'High',status:'Assigned',progress:15,crew:5,cost:65000,hours:4,owner:'Road clearance team',reason:'Open an access corridor for response vehicles.',dependency:'Confirm nearby wires are isolated',update:'Tree-removal crew assigned; access inspection pending.',steps:['Obstruction reported','Crew assigned','Tree removal','Road reopened after inspection'],risk:'Keep away from unstable trees and overhead wires.'},
{id:'SLM-1045',title:'Damaged mobile network tower',place:'Pallikaranai · service area',type:'Telecom',icon:'network',priority:'Medium',status:'Assessment',progress:5,crew:4,cost:320000,hours:18,owner:'Telecom restoration team',reason:'Restore communication after structure and access checks.',dependency:'Structural inspection required',update:'Structural review requested; temporary coverage plan pending.',steps:['Service loss logged','Structural assessment','Repair or temporary service','Coverage verified'],risk:'Stay outside the cordoned area.'},
{id:'SLM-1046',title:'Blocked roadside drain',place:'Vijaya Nagar · junction',type:'Drainage',icon:'water',priority:'Medium',status:'Resolved',progress:100,crew:3,cost:45000,hours:3,owner:'Drainage maintenance team',reason:'Remove a local blockage and confirm drainage flow.',dependency:'No open dependencies',update:'Drain cleared and flow checked in this demonstration record.',steps:['Blockage logged','Crew assigned','Debris removed','Flow checked and closure recorded'],risk:'Avoid open drains; follow barriers at the work site.'}
];
let issues=store.get('issues',issuesSeed);
function money(v){return new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(v)}
function toast(msg){const e=$('#toast');if(!e)return;e.textContent=msg;e.classList.add('visible');clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>e.classList.remove('visible'),5500)}
function badge(txt,type=''){return `<span class="tag ${type}">${esc(txt)}</span>`}
function nav(){return `<header class="topbar"><div class="wrap nav-inner"><a class="brand" href="index.html" aria-label="SOLUM home"><span class="brand-mark">${icon('layers')}</span>SOLUM</a><nav class="nav-links" aria-label="Primary navigation">${['prepare','resolve','report'].map(p=>`<a href="${p}.html" ${page===p?'class="active" aria-current="page"':''}>${p[0].toUpperCase()+p.slice(1)}</a>`).join('')}</nav>${page==='resolve'||page==='officials'?`<a class="btn-soft nav-action" href="officials.html">${icon('lock')} Officials access</a>`:`<button class="btn-soft nav-action" data-action="location">${icon('pin')} <span data-location-short>${esc(locationData.name)}</span></button>`}</div></header>`}
function footer(){return `<footer><div class="wrap"><div class="footer-top"><a class="brand" href="index.html"><span class="brand-mark">${icon('layers')}</span>SOLUM</a><div class="footer-links"><a href="prepare.html">Prepare</a><a href="resolve.html">Resolve</a><a href="report.html">Report</a><button class="text-link" data-action="sources" style="border:0;background:none;padding:0">Sources & transparency</button></div></div><div class="footer-bottom"><span>One view. Every layer. A safer tomorrow.</span><span>SOLUM · Data-Driven Decision Support & Google Maps 3D Platform.</span></div></div></footer>`}
function locationButton(){return `<button class="location-button" data-action="location">${icon('pin')}<span><small>YOUR LOCATION</small><b data-location-full>${esc(formatLocationDisplay(locationData))}</b></span><span>⌄</span></button>`}
const demoNote=(text='Live data connected. Scenario models, terrain intelligence, and repair records reflect connected backend and Google Maps 3D services.')=>`<div class="demo-note">${icon('info')}<p>${text}</p></div>`;
function pageHero(eyebrow,title,desc){return `<section class="page-hero wrap"><div class="breadcrumbs"><a href="index.html">Home</a> / ${page==='officials'?'Officials workspace':page[0].toUpperCase()+page.slice(1)}</div><div class="intro-top"><div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1><p>${desc}</p></div>${locationButton()}</div></section>`}
function home(){return `<main id="main"><section class="home-intro"><div class="wrap"><div class="intro-top"><div><span class="eyebrow plain">${icon('shield')} LAND INTELLIGENCE. HUMAN IMPACT.</span><h1>A little awareness.<br><span>A safer tomorrow.</span></h1><p style="margin:0;font-size:14px">Know what’s happening. Prepare with clarity. Recover together.</p></div>${locationButton()}</div><section class="news-panel" aria-label="Hazard news carousel"><div class="news-toolbar"><span class="breaking"><span class="dot-live"></span> Hazard news & updates</span><div class="tabs" id="news-tabs" aria-label="News region">${['district','state','national'].map((s,i)=>`<button class="${i===0?'active':''}" data-scope="${s}" aria-pressed="${i===0}">${s==='district'?'Near you':s==='state'?'State':'National'}</button>`).join('')}</div></div><div class="news-content"><div class="news-copy" id="news-copy"></div><div class="news-art"><img id="news-art-img" src="assets/images/news/waterbody-restoration.svg" alt="Civic news scene"><div class="art-label" id="news-art-caption">${icon('pin')} <span data-location-full>${esc(formatLocationDisplay(locationData))}</span> · Civic scene</div></div></div><div class="news-bottom"><span id="news-status">Connecting to source feeds…</span><div class="dots" id="news-dots"></div><div class="news-controls"><button id="news-prev" aria-label="Previous news">←</button><button id="news-pause" aria-label="Pause news slideshow">Ⅱ</button><button id="news-next" aria-label="Next news">→</button></div></div></section></div></section>
<section class="weather-section wrap"><div class="weather-box"><div class="weather-head"><h3>${icon('sun')} Your week, at a glance</h3><div class="row-flex"><span class="tag gray" id="weather-status">Connecting to weather…</span><button class="text-link" id="refresh-weather" style="border:0;background:none">Refresh ↻</button></div></div><div id="weather-content"></div><p class="weather-note" id="weather-note">Useful everyday weather. Forecasts can change; check official warnings before travel.</p></div></section>
<section class="story-section"><div class="wrap"><div class="story-heading"><div><span class="eyebrow plain">BEFORE THE NEXT STORM</span><h2>When the city changes,<br>your decisions matter.</h2></div><p>Floods don’t stop at a street. A blocked drain, a damaged power line, a closed road — every layer is connected. Explore why a shared view can make a difference.</p></div><div class="story-stage"><canvas id="story-canvas" aria-label="Animated isometric demonstration of flooding, landslides and cyclones" tabindex="0"></canvas><div class="scene-top"><span class="tag">${icon('layers')} SOLUM · CITY STORIES</span><span class="tag gray">3D awareness illustration</span></div><div class="scene-bottom"><div class="scene-caption"><h3 id="story-title">01 / When water finds a way.</h3><p id="story-desc">See how flooding can connect streets, homes and essential services.</p></div><div class="scene-controls" aria-label="Animation chapters"><button class="active" data-chapter="flood">Flood</button><button data-chapter="landslide">Landslide</button><button data-chapter="cyclone">Cyclone</button><button id="story-play" aria-label="Pause animation">Ⅱ</button></div></div></div><div class="story-progress"><div><b>01 — UNDERSTAND</b>See the place, not just the problem.</div><div><b>02 — PREPARE</b>Turn information into everyday actions.</div><div><b>03 — RECOVER</b>Reconnect the systems we depend on.</div></div></div></section>
<section class="section wrap"><div class="section-head"><div><span class="eyebrow plain">ONE PLACE. THREE CRITICAL MOMENTS.</span><h2>From knowing to doing.</h2></div><p>One location profile connects your preparation, your neighbourhood’s recovery, and tomorrow’s plans.</p></div><div class="grid-3">${[['01','shield','Prepare','Be ready, before it arrives.','Explore a place in 3D, understand potential hazards and build a practical household plan.'],['02','tool','Resolve','Recover, together.','Follow repair priorities, share overlooked problems and see how work moves forward.'],['03','report','Report','Build on better understanding.','Bring land, water and environmental context together before you plan a new building.']].map(a=>`<a class="card feature-card" href="${a[2].toLowerCase()}.html"><img src="assets/${a[2].toLowerCase()}-illustration.svg" alt="${a[2]} concept illustration" style="width:100%;height:155px;object-fit:cover;border-radius:13px;margin-bottom:22px"><div class="row-flex between"><span class="number">${a[0]} / SOLUM</span></div><h3>${a[2]}</h3><b style="font-size:13px">${a[3]}</b><p style="margin:10px 0 23px">${a[4]}</p><span class="text-link">Explore ${a[2].toLowerCase()} ${icon('arrow')}</span></a>`).join('')}</div></section>
<section class="section" style="background:#f0f6f1;padding-top:54px;padding-bottom:54px"><div class="wrap"><div class="section-head"><div><span class="eyebrow plain">LESS FRAGMENTATION. MORE CLARITY.</span><h2>Every layer tells part of the story.</h2></div><p>Terrain in one portal. Water in another. Reports in a PDF. SOLUM brings their relationships into one understandable view.</p></div><div class="flow" aria-label="Data to action workflow">${[['Select','Choose your location.'],['Assemble','Bring relevant layers together.'],['Analyse','Explain patterns and data gaps.'],['Explore','See the context in 3D.'],['Act','Make evidence-linked decisions.']].map((a,i)=>`<div class="flow-step"><span>${i+1}</span><b>${a[0]}</b><p>${a[1]}</p></div>`).join('')}</div><p class="source-line">Grounded GIS & Google Maps 3D Platform intelligence. A language model alone is not a disaster predictor.</p></div></section>
<section class="section wrap"><div class="trust-panel"><div><span class="eyebrow">TRUST YOU CAN TRACE</span><h2 style="margin-top:20px">Good decisions start<br>with information<br>you can question.</h2><p>Know where a finding came from, when it was retrieved and what it cannot tell you. Confidence should come from evidence, not a reassuring badge.</p><button class="btn-soft" data-action="sources" style="margin-top:12px">Explore our sources ${icon('arrow')}</button></div><div class="trust-list"><div class="trust-item">${icon('report')}<div><b>Source-linked, from the start.</b><p>News keeps its publisher and link. Forecasts name their provider. Every report carries a verifiable audit reference.</p></div></div><div class="trust-item">${icon('lock')}<div><b>Designed for tamper evidence.</b><p>Cryptographic SHA-256 retrieval receipts for live weather payloads and chronological audit logs for civic changes.</p></div></div><div class="trust-item">${icon('people')}<div><b>People remain in control.</b><p>Missing data stays visible. Officials verify field reports. Engineers validate land assessments before decisions are made.</p></div></div></div></div></section><div class="wrap cta"><div><h2>A clearer view. A better next step.</h2><p>Start with your neighbourhood. Prepare for what matters.</p></div><a class="btn" href="prepare.html">Explore your area ${icon('arrow')}</a></div></main>`}
function mapMarkup(){return `<div class="map-panel"><div id="gmp-3d-wrap" style="position:absolute;inset:0;width:100%;height:100%;display:none;z-index:1;"><div id="google-map-3d" style="width:100%;height:100%;position:absolute;inset:0;display:block;"></div><div id="google-map" style="width:100%;height:100%;position:absolute;inset:0;display:none;"></div><div id="map-notice-banner" class="map-notice-banner hidden"></div></div><canvas id="map-canvas" class="map-canvas" aria-label="Illustrative neighbourhood model. Drag to rotate." tabindex="0"></canvas><div class="map-image" id="satellite-layer"><img id="satellite-image" alt="Satellite basemap imagery for the selected location"><div class="image-error hidden" id="satellite-error">Satellite imagery could not load. Check your connection or return to 3D view.</div><div class="map-attribution">Google Maps Platform · Satellite 3D Context</div></div><div class="map-top"><div><b id="map-title">${esc(locationData.name)} · Photorealistic 3D</b><small id="map-subtitle">Google Maps 3D Platform · True satellite imagery & 3D buildings</small></div><div>${badge('GOOGLE MAPS 3D','amber')}<small id="map-mode-indicator">Photorealistic 3D</small></div></div><div class="map-layer-toggles"><label title="Toggle Rivers & Water Bodies"><input type="checkbox" id="layer-water" checked> Water Bodies</label><label title="Toggle 100m Flood Buffer Catchment"><input type="checkbox" id="layer-flood" checked> Flood Buffers</label><label title="Toggle 3D Perspective Tilt"><input type="checkbox" id="layer-tilt" checked> 3D Tilt</label><label title="Toggle Civic Repair Issues"><input type="checkbox" id="layer-issues" checked> Civic Issues</label></div><div class="map-zoom"><button data-zoom="in" aria-label="Zoom in">+</button><button data-zoom="out" aria-label="Zoom out">−</button><button data-zoom="tilt" aria-label="Toggle camera tilt">📐</button><button data-zoom="rotate" aria-label="Orbit / Rotate camera">↻</button><button data-zoom="orbit" aria-label="360° Cinematic Orbit" title="360° Cinematic Orbit">🌐</button><button data-zoom="reset" aria-label="Reset view">↺</button></div><div class="map-legend"><span><i class="legend-dot" style="background:#0ea5e9"></i>Water Bodies</span><span><i class="legend-dot" style="background:#f59e0b"></i>100m Buffer</span><span><i class="legend-dot" style="background:#ef4444"></i>Civic Issue</span></div><div class="map-modes" aria-label="Map display"><button class="active" data-map-mode="3d">3D view</button><button data-map-mode="2d">2D view</button><button data-map-mode="satellite">Satellite</button><button data-map-mode="water">Water bodies</button></div></div><div class="timeline-bar"><div class="timeline-top-row"><div><b style="font-size:12px;color:#112017">Scenario Simulation:</b> <span id="scenario-sub-title" style="font-size:11px;color:#5d7566">Physics-grounded environmental projection</span></div><div class="scenario-pills" id="scenario-pills"></div></div><div class="timeline-slider-row"><span>Now</span><input type="range" id="scenario-time" min="0" max="24" value="0" step="1"><span>+24h</span><b class="tag gray" id="scenario-label">Hour 0 · Baseline</b><button class="icon-btn" id="map-motion" aria-label="Play scenario simulation" title="Play / Pause simulation">▶</button><button class="icon-btn" id="scenario-reset" aria-label="Reset simulation" title="Reset to Hour 0">↺</button></div></div>`}
const checklistData=[['Essentials at home','home',['Store drinking water and ready-to-eat food.','Keep medicines, a first-aid kit and personal care items together.','Charge phones and power banks; keep a torch ready.','Put identity documents and essentials in waterproof bags.']],['A plan for everyone','people',['Agree on a family contact and a meeting place.','Plan assistance for children, older adults and people with disabilities.','Include pets and their supplies in your plan.','Check official notices before leaving; avoid flooded roads.']]];
function prepare(){return `<main id="main">${pageHero('PREPARE · BEFORE A DISASTER','A little preparation.<br>A lot more peace of mind.','Understand your surroundings, explore possible impacts and turn awareness into a practical plan.')}<div class="wrap">${demoNote('Google Maps 3D active. Use timeline slider to simulate environmental impact progression over 24 hours.')}${mapMarkup()}</div><section class="section wrap" style="padding-top:35px"><div class="section-head"><div><span class="eyebrow plain">YOUR PREPARATION BRIEF</span><h2>What could this mean for you?</h2></div><span class="tag amber">Scenario guidance · grounded intelligence</span></div><div class="analysis-summary"><div class="metric"><span>SCENARIO PROFILE</span><b id="brief-scenario">${esc(locationData.name)}</b><span id="brief-coords">${locationData.lat.toFixed(3)}°N, ${locationData.lon.toFixed(3)}°E · ${esc(formatLocationDisplay(locationData))}</span></div><div class="metric"><span>SIMULATION STAGE</span><b id="brief-timing">Hour 0 · Baseline</b><span id="brief-stage">Normal weather & drainage capacity</span></div><div class="metric"><span>HAZARD EXPOSURE</span><b id="brief-exposure">All Corridors Open</b><span id="brief-advisory">Follow designated municipal evacuation routes</span></div></div><div class="card scenario-card" id="scenario-detail-card" style="margin-bottom:28px;"><div class="row-flex between" style="margin-bottom:14px;flex-wrap:wrap"><div><span class="eyebrow" id="sim-scenario-type">PHYSICS-GROUNDED SCENARIO</span><h3 id="sim-scenario-title" style="margin:8px 0 0;font-size:18px">Loading simulation…</h3></div><div id="sim-severity-badge"><span class="tag">Low Exposure</span></div></div><p id="sim-narrative" style="font-size:13px;line-height:1.55;color:#284333;margin-bottom:18px;">At Hour 0, surface runoff in the drainage basin is operating within standard municipal capacity.</p><div class="sim-metrics-grid" id="sim-metrics-grid"><div class="sim-metric-item"><small>Rainfall Accum.</small><b id="metric-rain">0 mm</b></div><div class="sim-metric-item"><small>Peak Wind Gust</small><b id="metric-wind">0 km/h</b></div><div class="sim-metric-item"><small>Soil Saturation</small><b id="metric-soil">0 %</b></div><div class="sim-metric-item"><small>Water Volume</small><b id="metric-vol">0 m³</b></div><div class="sim-metric-item"><small>Affected Area</small><b id="metric-area">0 km²</b></div></div><div class="grid-2" style="margin-top:20px;"><div><b style="font-size:12px;display:block;margin-bottom:8px;color:#10291e">INTERSECTING ARTERIAL CORRIDORS</b><div id="sim-roads-list" style="display:grid;gap:6px;"></div></div><div><b style="font-size:12px;display:block;margin-bottom:8px;color:#10291e">CRITICAL FACILITIES & UTILITIES AT RISK</b><div id="sim-facilities-list" style="display:grid;gap:6px;"></div></div></div><div class="subtle" id="sim-assumptions" style="margin-top:20px;font-size:11px;line-height:1.5;"><b>Model Assumptions & Data Grounding:</b> Evaluated on Copernicus DEM 30m terrain contours and India-WRIS hydrological distances. Not an operational disaster forecast; always follow official emergency instructions from civil defence authorities.</div></div><div class="grid-2">${checklistData.map((a,ix)=>`<div class="card action-card"><h3>${icon(a[1])} ${a[0]}</h3><ul class="checklist">${a[2].map((t,i)=>`<li><input type="checkbox" id="check-${ix}-${i}" data-check="${ix}-${i}"><label for="check-${ix}-${i}">${t}</label></li>`).join('')}</ul></div>`).join('')}</div><div class="grid-2" style="margin-top:22px"><div class="card"><h3>${icon('pin')} Movement & shelter</h3><p style="font-size:13px">Do not enter or drive through floodwater. If evacuation is directed, follow the route and shelter information from local authorities. A familiar road may no longer be safe.</p><a class="text-link" href="https://chennaicorporation.gov.in/" target="_blank" rel="noopener">Greater Chennai Corporation ${icon('arrow')}</a></div><div class="card"><h3>${icon('layers')} How land risk models work</h3><p style="font-size:13px">Validated rainfall forecasts, elevation, drainage, satellite observations and historical events inform the SOLUM geospatial due-diligence engine.</p><button class="text-link" data-action="sources" style="border:0;background:none;padding:0">See evidence & data gaps ${icon('arrow')}</button></div></div><p class="source-line">Preparedness guidance: <a href="https://mausam.imd.gov.in/chennai/mcdata/dos%26donts.pdf" target="_blank" rel="noopener">IMD Chennai — Floods: Dos and Don’ts</a>. Follow current instructions from local authorities.</p></section><section class="chat-section" style="background:#edf6ef"><div class="wrap"><span class="eyebrow">${icon('shield')} ASK SOLUM</span><h2 style="margin:15px 0 9px">A question today. More clarity tomorrow.</h2><p>Ask about preparation, supplies, routes or what the map means.</p><div class="chat-shell"><div class="chat-log" id="chat-log" aria-live="polite"><div class="bubble">Hello! I am your SOLUM Decision Support Guide. I can share source-linked preparedness guidance, safety precautions, and land assessment insights. What would you like to know?</div></div><form class="chat-form" id="chat-form"><input id="chat-input" aria-label="Ask a preparation question" placeholder="What should I keep in my emergency bag?" maxlength="500" required><button class="btn" type="submit">Ask ${icon('arrow')}</button></form><div class="suggestions"><button data-question="What should I pack?">Emergency bag</button><button data-question="Which route is safe?">Safe routes</button><button data-question="When will the flood arrive?">Flood timing</button><button data-question="What are your data sources?">Data sources</button></div></div></div></section></main>`}
function resolve(){return `<main id="main">${pageHero('RESOLVE · AFTER A DISASTER','Recovery you can follow.','See what needs attention, understand the work underway and help bring overlooked problems into view.')}<section class="wrap" style="padding-bottom:70px"><div class="row-flex between" style="margin:16px 0;flex-wrap:wrap"><span class="small muted">${icon('pin')} Selected location: <b data-location-full>${esc(formatLocationDisplay(locationData))}</b></span><span class="tag gray">Connected SQLite Database</span></div>${demoNote('Civic repair records are stored in the persistent backend database. Complaints submitted here are saved with coordinates and media attachments.')}<div class="resolve-stats" id="resolve-stats"></div><div class="section-head"><h2 style="font-size:25px">Your neighbourhood, in progress.</h2><label class="small">Show <select id="issue-filter" style="padding:8px;border:1px solid #dce7df;border-radius:8px;margin-left:8px"><option value="all">All issues</option><option value="open">Open issues</option><option value="Resolved">Resolved</option><option value="Electricity">Electricity</option><option value="Drainage">Drainage</option><option value="Roads">Roads</option></select></label></div><div class="issues-layout"><div><div class="small muted" style="margin-bottom:12px">REPORTED PROBLEMS</div><div class="issue-list" id="issue-list"></div></div><article class="card issue-detail" id="issue-detail" aria-live="polite"></article></div><div class="complaint-cta"><div><h3>Something still needs attention?</h3><p>Share the problem, its location and supporting photos or videos.</p></div><button class="btn" data-action="complaint">Raise a Complaint ${icon('arrow')}</button></div><div class="subtle" style="margin-top:20px">${icon('shield')} Every issue has a verified ID, a responsible team, and a change history recorded in the database.</div></section></main>`}
function report(){return `<main id="main">${pageHero('REPORT · BEFORE YOU BUILD','Understand the land.<br>Before you build on it.','A clearer starting point for homeowners, builders and planners — backed by geospatial terrain, water proximity & flood analysis.')}<section class="wrap section" style="padding-top:15px"><div class="card report-form"><form id="land-form"><h3>Start a land assessment</h3><p style="font-size:13px">Choose the site and proposed use. We’ll compute real terrain elevation, slope, and waterbody buffers across Tamil Nadu.</p><div class="field"><label for="land-address">Site / locality</label><input id="land-address" value="${esc(formatLocationDisplay(locationData))}" required maxlength="160" placeholder="Locality, district, state"></div><div class="form-grid"><div class="field"><label for="land-use">Proposed use</label><select id="land-use"><option>Individual home</option><option>Apartment building</option><option>Commercial building</option><option>Community facility</option></select></div><div class="field"><label for="land-area">Plot area (m²)</label><input type="number" min="1" max="10000000" id="land-area" value="240" required></div><div class="field"><label for="land-lat">Latitude</label><input id="land-lat" type="number" min="-90" max="90" step="any" value="${locationData.lat.toFixed(4)}" required></div><div class="field"><label for="land-lon">Longitude</label><input id="land-lon" type="number" min="-180" max="180" step="any" value="${locationData.lon.toFixed(4)}" required></div></div><button class="btn" type="submit">Compute land assessment ${icon('arrow')}</button><p class="source-line">Coordinates are evaluated with Copernicus DEM elevation, Shapely waterbody buffers, and Tamil Nadu regional hazard models.</p></form><div class="report-visual"><img src="assets/city.svg" alt="Illustrated land, buildings and water corridor"><h3 style="margin-top:16px">The whole place.<br>Not just the plot.</h3><p>Consider terrain, water, drainage, access and environmental constraints together. Missing evidence is a question to investigate, not a green light to build.</p></div></div><div class="report-result hidden" id="report-result" aria-live="polite"></div><div class="section-head" style="margin-top:55px"><div><span class="eyebrow plain">A BETTER STARTING POINT</span><h2 style="font-size:28px">Ask the questions that matter.</h2></div></div><div class="grid-3">${[['water','Water & drainage','Look beyond a plot boundary. Ask about flood history, drainage connectivity, water bodies and seasonal groundwater.'],['layers','Ground & terrain','Confirm levels, soil bearing capacity and slope conditions through appropriate surveys and engineering tests.'],['report','Rules & approvals','Verify land classification, access rights, setbacks and applicable environmental or coastal restrictions.']].map(a=>`<div class="card"><div class="feature-icon">${icon(a[0])}</div><h3>${a[1]}</h3><p style="font-size:13px;margin:0">${a[2]}</p></div>`).join('')}</div></section></main>`}
function officials(){return `<main id="main">${pageHero('RESOLVE · OFFICIALS WORKSPACE','Coordinate the work.<br>Reconnect the city.','Authorized coordination dashboard for municipal response teams: dependencies first, location-specific priorities, and server-authorized updates.')}<div class="wrap">${demoNote('Civic Coordination Workspace connected to FastAPI backend. Published updates persist in SQLite and are logged in the audit trail.')}</div><section class="card login-panel" id="official-login"><div class="feature-icon">${icon('lock')}</div><h2 style="font-size:27px">Officials access</h2><p style="font-size:13px">Authorized municipal coordination portal for Tamil Nadu civic disaster & infrastructure teams.</p><form id="official-login-form"><div class="field"><label for="official-id">Official ID</label><input id="official-id" value="OFF-CH-02" required maxlength="30" placeholder="e.g. OFF-CH-02, OFF-CB-03, OFF-TN-01"><small style="color:#5d7566">Demo Accounts: <b>OFF-TN-01</b> (State Commissioner · All TN), <b>OFF-CH-02</b> (Chennai), <b>OFF-CB-03</b> (Coimbatore), <b>OFF-MD-04</b> (Madurai), <b>OFF-SL-05</b> (Salem), <b>OFF-NL-07</b> (Nilgiris)</small></div><div class="field"><label for="official-passcode">Security Passcode</label><input id="official-passcode" type="password" value="SOLUM-TN-2026" required placeholder="Authorized passcode"></div><div class="form-grid"><div class="field"><label for="official-role">Designation / Role</label><select id="official-role"><option value="District coordination officer">District coordination officer</option><option value="State Disaster Commissioner">State Disaster Commissioner</option><option value="Infrastructure repair lead">Infrastructure repair lead</option><option value="Rescue team coordinator">Rescue team coordinator</option></select></div><div class="field"><label for="official-district">Jurisdiction District</label><select id="official-district"><option value="Chennai">Chennai</option><option value="Coimbatore">Coimbatore</option><option value="Madurai">Madurai</option><option value="Salem">Salem</option><option value="Tiruchirappalli">Tiruchirappalli</option><option value="Nilgiris">Nilgiris</option><option value="All-TN">All-TN (Statewide)</option></select></div></div><button class="btn" style="width:100%">Authenticate & Enter Workspace ${icon('arrow')}</button></form><p class="source-line">Protected with HMAC-SHA256 session tokens. Unauthorized cross-district operations are blocked by server-side authorization.</p></section><section class="wrap section hidden" id="official-workspace" style="padding-top:15px"><div class="row-flex between" style="margin-bottom:20px;flex-wrap:wrap"><span class="tag" id="official-role-label"></span><button class="btn-ghost" id="official-logout" style="font-size:12px;padding:8px 16px">Exit workspace</button></div><div class="official-stats-grid" id="official-stats-grid"></div><div class="officer-grid"><div class="card"><div class="row-flex between"><h3 style="margin:0">Suggested repair priorities</h3>${badge('DYNAMIC RANKING','amber')}</div><p style="font-size:12px;margin-top:12px">Life safety → service dependencies → access → restoration. Dynamically prioritized by the backend system.</p><div id="priority-list"></div></div><div class="card"><h3>Resources at a glance</h3><div class="field"><label for="available-funds">Available funds (₹)</label><input id="available-funds" type="number" min="0" max="1000000000" value="1000000"></div><div class="field"><label for="available-crew">Available crew members</label><input id="available-crew" type="number" min="0" max="10000" value="24"></div><div id="budget-summary"></div><button class="btn-soft" id="export-plan" style="margin-top:20px;width:100%">${icon('download')} Export resource plan</button><p class="source-line">Generates a structured recovery allocation plan via FastAPI backend.</p></div></div><div class="grid-2" style="margin-top:24px"><form class="card" id="publish-form"><h3>Share a progress update</h3><div class="field"><label for="update-issue">Issue</label><select id="update-issue"></select></div><div class="form-grid"><div class="field"><label for="update-status">Status</label><select id="update-status"><option>Assessment</option><option>Assigned</option><option>In progress</option><option>Resolved</option></select></div><div class="field"><label for="update-progress">Progress (%)</label><input id="update-progress" type="number" min="0" max="100" value="45" required></div></div><div class="form-grid"><div class="field"><label for="update-crew">Assigned crew members</label><input id="update-crew" type="number" min="0" max="10000" value="8" required></div><div class="field"><label for="update-cost">Estimated work cost (₹)</label><input id="update-cost" type="number" min="0" max="1000000000" value="240000" required></div><div class="field"><label for="update-hours">Estimated work hours</label><input id="update-hours" type="number" min="0" max="8760" value="6" required></div><div class="field"><label for="update-owner">Responsible team</label><input id="update-owner" maxlength="100" required></div></div><div class="field"><label for="update-note">Public update</label><textarea id="update-note" required maxlength="500" placeholder="What has been done? What happens next?"></textarea></div><button class="btn">Publish database update ${icon('arrow')}</button><p class="source-line">Updates sync immediately across all connected citizens.</p></form><div class="card"><h3>Prevent the next disruption</h3><div class="flow" style="grid-template-columns:1fr;margin:20px 0"><div class="subtle">1 · Isolate damaged electricity infrastructure.</div><div class="subtle">2 · Confirm clearance before pumping floodwater.</div><div class="subtle">3 · Clear priority access for response vehicles.</div><div class="subtle">4 · Inspect repairs before restoring services.</div></div><h3 style="font-size:15px">Database Audit History</h3><div id="audit-log" style="font-size:12px;color:#64766b"></div></div></div></section></main>`}
function dialogs(){return `<dialog id="location-dialog"><div class="dialog-head"><h2>Start with your location.</h2><button data-close aria-label="Close location dialog">×</button></div><p style="font-size:13px">Use device GPS, search any Tamil Nadu city or locality, or enter direct coordinates.</p><button class="btn-soft" id="use-location" style="width:100%">${icon('pin')} Use my current location</button><form id="location-search-form" style="margin-top:16px"><div class="field"><label for="location-query">Search Tamil Nadu (City, District or Lat/Lon)</label><input id="location-query" placeholder="e.g. Ooty, Madurai, or 11.41, 76.69" required minlength="2" maxlength="100"></div><button class="btn" type="submit">Search ${icon('search')}</button></form><div class="tn-pills-wrap"><div class="tn-pills-title">Tamil Nadu Quick Select:</div><div class="tn-pills">${['Chennai','Coimbatore','Madurai','Tiruchirappalli','Salem','Tirunelveli','Vellore','Erode','Thanjavur','Tiruppur','Hosur','Kanchipuram','Chengalpattu','Ooty','Kodaikanal','Nagercoil','Cuddalore'].map(c=>`<button type="button" class="tn-pill-btn" data-tn-city="${c}">${c}</button>`).join('')}</div></div><div id="location-results" class="location-results" aria-live="polite"></div><button class="text-link" id="chennai-default" style="background:none;border:0;padding:6px 0 0">Use Chennai example</button></dialog>
<dialog id="complaint-dialog"><div class="dialog-head"><h2>Raise a Complaint</h2><button data-close aria-label="Close complaint dialog">×</button></div><div id="complaint-form-wrap"><p style="font-size:13px">Civic ticket submission — saved to SOLUM database with coordinates and photos.</p><form id="complaint-form"><div class="field"><label for="complaint-subject">Subject</label><input id="complaint-subject" required maxlength="100" placeholder="e.g. Fallen tree blocking our street"></div><div class="form-grid"><div class="field"><label for="complaint-category">Category</label><select id="complaint-category"><option>Roads</option><option>Electricity</option><option>Drainage</option><option>Telecom</option><option>Other</option></select></div><div class="field"><label for="complaint-place">Location / landmark</label><input id="complaint-place" required maxlength="160" placeholder="Street, locality, landmark"></div></div><div class="field"><label for="complaint-description">Description</label><textarea id="complaint-description" required minlength="10" maxlength="1000" placeholder="Describe the problem and who is affected."></textarea></div><div class="field"><label for="complaint-evidence">Photos or videos (optional)</label><input id="complaint-evidence" type="file" accept="image/*,video/*" multiple><small>Up to 3 files, 10 MB each. Uploaded securely to backend storage.</small></div><div class="media-preview" id="media-preview"></div><button class="btn" type="submit" style="margin-top:15px">Submit complaint ${icon('arrow')}</button></form></div><div id="complaint-success" class="hidden"></div></dialog>
<dialog id="sources-dialog"><div class="dialog-head"><h2>Evidence, not just answers.</h2><button data-close aria-label="Close sources dialog">×</button></div><p style="font-size:13px">Live feeds retain provider links and retrieval status. A cryptographic digest helps compare a retrieved response.</p><div class="source-cards"><a href="https://developers.google.com/maps/documentation/javascript/3d-maps" target="_blank" rel="noopener">Google Maps 3D Platform ↗<small>Photorealistic 3D Maps & Web Components</small></a><a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo ↗<small>Forecast API · CC BY 4.0 · 7-day weather model</small></a><a href="https://mausam.imd.gov.in/chennai/" target="_blank" rel="noopener">IMD Regional Meteorological Centre, Chennai ↗<small>Official weather warnings and bulletins</small></a><a href="https://www.gdacs.org/" target="_blank" rel="noopener">GDACS ↗<small>Global disaster alerts and crisis coordination</small></a><a href="https://chennaicorporation.gov.in/" target="_blank" rel="noopener">Greater Chennai Corporation ↗<small>Civic authority information</small></a><a href="https://bhuvan.nrsc.gov.in/" target="_blank" rel="noopener">ISRO Bhuvan ↗<small>Geoportal reference data</small></a></div><div class="subtle" style="margin-top:18px"><b>Connected Backend Services</b><br>FastAPI asynchronous backend, SQLite relational database with WAL mode, Shapely geospatial terrain processing, and Google Maps 3D Platform.</div><details style="font-size:11px;margin-top:15px"><summary>Latest weather retrieval receipt</summary><pre id="weather-receipt" style="white-space:pre-wrap;word-break:break-word">No live weather response retrieved yet.</pre></details></dialog>
<button type="button" id="solum-ai-trigger" class="solum-ai-floating-btn" aria-label="Open SOLUM AI Assistant" title="Ask SOLUM AI"><span class="solum-ai-badge-dot"></span>${icon('shield')} Ask SOLUM AI</button>
<aside id="solum-ai-panel" class="solum-ai-panel hidden" aria-label="SOLUM AI Assistant" role="dialog"><header class="solum-ai-header"><div class="solum-ai-header-info"><div class="solum-ai-avatar">${icon('shield')}</div><div class="solum-ai-header-title"><h4>SOLUM AI</h4><span>Grounded Land & Disaster Intelligence</span></div></div><div style="display:flex;align-items:center;gap:6px"><button type="button" id="solum-ai-clear" title="Clear Chat History" style="border:none;background:none;font-size:12px;color:#64766b;cursor:pointer">Clear</button><button type="button" id="solum-ai-close" class="solum-ai-close" aria-label="Close Assistant">×</button></div></header><div class="solum-ai-body" id="solum-ai-body"><div class="solum-ai-msg bot">Hello! I am <b>SOLUM AI</b>, your grounded geospatial assistant for Tamil Nadu. I can explain land assessments, compare flood exposure across districts, guide civic complaint reporting, or walk through 3D scenario simulations.<div class="solum-ai-actions"><button type="button" class="solum-ai-action-btn" data-solum-q="Explain flood risks in Madurai vs Chennai">Madurai vs Chennai</button><button type="button" class="solum-ai-action-btn" data-solum-q="What is the 100m waterbody buffer rule?">100m Water Buffer</button><button type="button" class="solum-ai-action-btn" data-solum-q="How do I raise a complaint for fallen wires?">Report Wire Hazard</button></div></div></div><div class="solum-ai-quick-chips"><button type="button" data-solum-q="Explain my land assessment">Land Assessment</button><button type="button" data-solum-q="What is the difference between elevation and slope?">Elevation vs Slope</button><button type="button" data-solum-q="What should I pack in an emergency bag?">Emergency Kit</button><button type="button" data-solum-q="How do officials coordinate repairs?">Official Repair Flow</button></div><form class="solum-ai-footer" id="solum-ai-form"><input type="text" id="solum-ai-input" class="solum-ai-input" placeholder="Ask about terrain, floods, complaints, or safety…" maxlength="600" autocomplete="off" required><button type="submit" class="solum-ai-send">${icon('arrow')}</button></form></aside><div id="toast" class="toast" role="status" aria-live="polite"></div>`}

document.getElementById('app').innerHTML=nav()+({index:home,prepare,resolve,report,officials}[page]||home)()+footer()+dialogs();

document.addEventListener('click',e=>{
  const close=e.target.closest('[data-close]');
  if(close)close.closest('dialog').close();
  const a=e.target.closest('[data-action]');
  if(!a)return;
  const type=a.dataset.action;
  if(type==='complaint'){
    $('#complaint-form-wrap').classList.remove('hidden');
    $('#complaint-success').classList.add('hidden');
    $('#complaint-place').value=formatLocationDisplay(locationData);
  }
  $('#'+type+'-dialog')?.showModal();
});

$$('dialog').forEach(d=>d.addEventListener('click',e=>{
  if(e.target===d){
    const r=d.getBoundingClientRect();
    if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();
  }
}));

async function api(path, options={}){
  const res=await fetch(path,{...options, signal:AbortSignal.timeout(18000)});
  if(!res.ok)throw Error('Service unavailable');
  return res.json();
}

function updateLocation(l){
  locationData=l;
  store.set('location',l);
  const shortName=formatShortLocation(l);
  const fullName=formatLocationDisplay(l);
  $$('[data-location-short]').forEach(e=>e.textContent=shortName);
  $$('[data-location-full]').forEach(e=>e.textContent=fullName);
  $('#location-dialog')?.close();
  toast(`Location updated to ${fullName}. Fetching contextual data…`);
  
  if(page==='index'){loadNews();loadWeather();}
  if(page==='prepare'){
    if($('#brief-scenario'))$('#brief-scenario').textContent = l.name;
    if($('#brief-coords'))$('#brief-coords').textContent = `${l.lat.toFixed(3)}°N, ${l.lon.toFixed(3)}°E`;
    if(activeMapMode==='3d' && googleMap3D && typeof googleMap3D.flyCameraTo === 'function'){
      try{
        googleMap3D.flyCameraTo({
          endCamera:{center:{lat:l.lat, lng:l.lon, altitude:35}, tilt:65, heading:20, range:1200},
          durationMillis:2200
        });
      }catch(e){}
      $('#map-title').textContent = `${l.name} · Photorealistic 3D`;
      $('#map-subtitle').textContent = 'Google Maps 3D Platform · True 3D terrain & aerial photorealistic mesh';
    }
    if(googleMap){
      googleMap.panTo({lat: l.lat, lng: l.lon});
      if(activeMapMode!=='3d'){
        $('#map-title').textContent = `${l.name} · ${activeMapMode==='satellite'?'2D Satellite Basemap':activeMapMode==='2d'?'2D Civic Plan':'Water Bodies & Corridors'}`;
      }
      loadMapOverlays(l.lat, l.lon);
    }
    loadMapMarkers();
    if($('#satellite-layer')?.style.display==='block')loadSatellite();
    initSimulation('auto');
  }
  if(page==='resolve'){
    renderResolve();
  }
  if(page==='report'){
    if($('#land-address'))$('#land-address').value = fullName;
    if($('#land-lat'))$('#land-lat').value = l.lat.toFixed(4);
    if($('#land-lon'))$('#land-lon').value = l.lon.toFixed(4);
  }
  if(page==='officials'){
    renderOfficial();
  }
  if($('#complaint-place'))$('#complaint-place').value = fullName;
  if($('#news-art-caption'))$('#news-art-caption').innerHTML = `${icon('pin')} <span data-location-full>${esc(fullName)}</span> · Civic scene`;
}

$('#chennai-default').addEventListener('click',()=>updateLocation({...defaults}));

$$('[data-tn-city]').forEach(b=>b.onclick=async()=>{
  const cityName=b.dataset.tnCity;
  $('#location-results').textContent='Loading '+cityName+'…';
  try{
    const data=await api('/api/geocode?q='+encodeURIComponent(cityName));
    const p=data.results?.[0];
    if(p){
      updateLocation({name:p.name,district:p.admin2||p.name,state:p.admin1||'Tamil Nadu',country:p.country||'India',lat:p.latitude,lon:p.longitude,mode:'Selected city'});
    }
  }catch{
    toast('Unable to switch to '+cityName);
  }
});

$('#location-search-form').addEventListener('submit',async e=>{
  e.preventDefault();
  const q=$('#location-query').value.trim();
  $('#location-results').textContent='Finding locations across Tamil Nadu…';
  try{
    const data = await api('/api/geocode?q='+encodeURIComponent(q));
    const places = data.results||[];
    $('#location-results').innerHTML = places.length?places.map((p,i)=>`<button data-place-index="${i}">${esc(p.name)}<small>${esc([p.admin2,p.admin1,p.country].filter(Boolean).join(', '))}</small></button>`).join(''):'No matching city found. Try a nearby city, district, or coordinates (e.g. 11.41, 76.69).';
    $$('[data-place-index]').forEach(b=>b.onclick=()=>{
      const p=places[+b.dataset.placeIndex];
      updateLocation({name:p.name,district:p.admin2||p.name,state:p.admin1||'Tamil Nadu',country:p.country||'India',lat:p.latitude,lon:p.longitude,mode:'Selected city'});
    });
  }catch{
    $('#location-results').textContent='Location search is unavailable. Check your connection or use the Chennai example.';
  }
});

$('#use-location').addEventListener('click',()=>{
  if(!navigator.geolocation){
    toast('Your browser does not support device location. Search for a city instead.');
    return;
  }
  $('#location-results').textContent='Waiting for device location permission…';
  navigator.geolocation.getCurrentPosition(async p=>{
    const lat=p.coords.latitude,lon=p.coords.longitude;
    let l={name:`${lat.toFixed(3)}°, ${lon.toFixed(3)}°`,district:'',state:'',country:'',lat,lon,mode:'Device coordinates',accuracy:Math.round(p.coords.accuracy)};
    try{
      const r=await api('/api/reverse?lat='+lat+'&lon='+lon),a=r.address||{};
      l={...l,name:a.city||a.town||a.village||a.suburb||l.name,district:a.state_district||a.county||a.city||'',state:a.state||'',country:a.country||''};
    }catch{}
    updateLocation(l);
  },err=>{$('#location-results').textContent=err.code===1?'Location permission was declined. Search a city instead.':'Unable to determine your location. Search a city or use Chennai.';},{enableHighAccuracy:false,timeout:12000,maximumAge:300000});
});

function fallbackNews(){
  return[
    {title:'Stay informed before the weather changes.',summary:'Open official bulletins for current warnings. Live news is unavailable here; this is an evergreen preparedness resource, not a breaking alert.',publisher:'IMD Chennai',url:'https://mausam.imd.gov.in/chennai/',kind:'SOURCE DIRECTORY',published:null,image_url:'assets/images/news/monsoon-radar.svg',image_caption:'IMD Doppler Radar & Monsoon Tracking · Tamil Nadu'},
    {title:'A ready household starts with a simple plan.',summary:'Review official flood preparedness guidance and agree on a family contact. No local disaster is implied by this card.',publisher:'IMD · preparedness guidance',url:'https://mausam.imd.gov.in/chennai/mcdata/dos%26donts.pdf',kind:'PREPAREDNESS RESOURCE',published:null,image_url:'assets/images/news/waterbody-restoration.svg',image_caption:'Basin Hydrology & Flood Inundation Buffer Model'},
    {title:'Know where to find local authority updates.',summary:'Consult your local authority for verified road restrictions, shelter notices and service-restoration updates.',publisher:'Greater Chennai Corporation',url:'https://chennaicorporation.gov.in/',kind:'CHENNAI SOURCE DIRECTORY',published:null,image_url:'assets/images/news/stormwater-drainage.svg',image_caption:'Municipal Stormwater Drainage & Culvert Network'}
  ];
}

function renderNews(){
  if(!newsItems.length)return;
  newsIndex=(newsIndex+newsItems.length)%newsItems.length;
  const n=newsItems[newsIndex];
  $('#news-copy').innerHTML=`${badge(n.kind||'LATEST COVERAGE',n.kind==='BREAKING'?'red':'amber')}<h2>${esc(n.title)}</h2><p>${esc(n.summary||'Open the publisher’s report for the full context. News coverage is not an official emergency instruction.')}</p><div class="news-meta"><span>${esc(n.publisher||'Source')}</span><span>·</span><span>${n.published?esc(new Date(n.published).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})):'Reference resource'}</span><a class="text-link" href="${esc(safeURL(n.url))}" target="_blank" rel="noopener">Read source ↗</a></div>`;
  $('#news-dots').innerHTML=newsItems.map((_,i)=>`<button class="${i===newsIndex?'active':''}" data-news-index="${i}" aria-label="Show news item ${i+1}" aria-pressed="${i===newsIndex}"></button>`).join('');
  $$('[data-news-index]').forEach(b=>b.onclick=()=>{newsIndex=+b.dataset.newsIndex;renderNews()});
  
  const imgEl=$('#news-art-img'),capEl=$('#news-art-caption');
  if(imgEl){
    imgEl.src=n.image_url||'assets/images/news/waterbody-restoration.svg';
    imgEl.alt=n.title||'Civic hazard news illustration';
  }
  if(capEl){
    capEl.innerHTML=`${icon('pin')} <span data-location-full>${esc(n.image_caption||(formatLocationDisplay(locationData)+' · Civic scene'))}</span>`;
  }
}

async function loadNews(){
  const gen=++newsGeneration;
  newsItems=fallbackNews();
  newsIndex=0;
  renderNews();
  $('#news-status').textContent='Connecting to source feeds…';
  const region=newsScope==='national'?(locationData.country||'India'):newsScope==='state'?(locationData.state||locationData.name):(locationData.district||locationData.name);
  try{
    const d=await api('/api/news?region='+encodeURIComponent(region)+'&scope='+newsScope);
    if(gen!==newsGeneration)return;
    if(!d.items?.length)throw Error('No coverage');
    newsItems=d.items;
    newsIndex=0;
    renderNews();
    $('#news-status').textContent=`${d.cached?'Cached':'Retrieved'} ${new Date(d.retrieved_at).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})} · ${region} · ${d.items.length} reports`;
  }catch{
    if(gen!==newsGeneration)return;
    $('#news-status').textContent='Live feed unavailable · reference resources shown';
  }
}

const weatherSymbol=c=>c===0?'☀':c<=3?'⛅':c>=95?'⛈':c>=51?'☂':'☁';

function weatherPlaceholder(){
  return `<div class="weather-main"><div class="weather-current"><small class="muted">${esc(locationData.name)}</small><div class="temp">${icon('sun')} —°</div><span class="small muted">Live forecast unavailable</span></div><div class="weather-days">${Array.from({length:7},(_,i)=>{const d=new Date();d.setDate(d.getDate()+i);return `<div class="day"><small>${i===0?'Today':d.toLocaleDateString(undefined,{weekday:'short'})}</small><span class="weather-symbol" style="color:#a3b6a7">☁</span><b>—° / —°</b><small>Rain —%</small><br><small>UV —</small></div>`}).join('')}</div></div>`;
}

async function loadWeather(){
  const gen=++weatherGeneration;
  $('#weather-content').innerHTML=weatherPlaceholder();
  $('#weather-status').textContent='Connecting…';
  $('#weather-status').className='tag gray';
  try{
    const d=await api('/api/weather?lat='+locationData.lat+'&lon='+locationData.lon);
    if(gen!==weatherGeneration)return;
    if(!d.daily?.time||!d.current)throw Error('Incomplete data');
    const days=d.daily;
    $('#weather-content').innerHTML=`<div class="weather-main"><div class="weather-current"><small class="muted">${esc(locationData.name)} · ${esc(d.timezone||'local time')}</small><div class="temp">${icon('sun')} ${Math.round(d.current.temperature_2m)}°</div><span class="small muted">${weatherSymbol(d.current.weather_code)} Current weather model</span></div><div class="weather-days">${days.time.map((t,i)=>`<div class="day"><small>${i===0?'Today':new Date(t+'T12:00:00').toLocaleDateString(undefined,{weekday:'short'})}</small><span class="weather-symbol">${weatherSymbol(days.weather_code[i])}</span><b>${Math.round(days.temperature_2m_max[i])}° <span style="color:#8b9b91;font-weight:400">${Math.round(days.temperature_2m_min[i])}°</span></b><small>Rain ${days.precipitation_probability_max[i]??'—'}%</small><br><small>UV ${days.uv_index_max[i]??'—'}</small></div>`).join('')}</div></div>`;
    $('#weather-status').textContent='Forecast connected';
    $('#weather-status').className='tag';
    $('#weather-note').innerHTML=`${icon('info')} Daily high / low in °C · UV is the daily maximum · <a href="https://open-meteo.com/" target="_blank" rel="noopener" style="text-decoration:underline">Open-Meteo (CC BY 4.0)</a> · Retrieved ${new Date(d.retrieved_at||Date.now()).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}. Forecasts are not local hazard warnings.`;
    $('#weather-receipt').textContent=JSON.stringify({provider:'Open-Meteo',retrieved_at:d.retrieved_at||new Date().toISOString(),latitude:d.latitude,longitude:d.longitude,sha256:d.receipt_sha256||'Direct receipt'},null,2);
  }catch{
    if(gen!==weatherGeneration)return;
    $('#weather-status').textContent='Offline / unavailable';
    $('#weather-note').textContent='No current values are available. Start SOLUM with the backend launcher and connect to the internet.';
  }
}

function initHome(){
  loadNews();
  loadWeather();
  $('#refresh-weather').onclick=loadWeather;
  $$('[data-scope]').forEach(b=>b.onclick=()=>{
    newsScope=b.dataset.scope;
    $$('[data-scope]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b)});
    loadNews();
  });
  $('#news-prev').onclick=()=>{newsIndex--;renderNews()};
  $('#news-next').onclick=()=>{newsIndex++;renderNews()};
  const setPause=()=>{
    $('#news-pause').textContent=newsPaused?'▶':'Ⅱ';
    $('#news-pause').setAttribute('aria-label',newsPaused?'Play news slideshow':'Pause news slideshow');
  };
  setPause();
  $('#news-pause').onclick=()=>{newsPaused=!newsPaused;setPause()};
  setInterval(()=>{
    if(!newsPaused&&document.visibilityState==='visible'&&!$('.news-panel').matches(':hover')&&!$('.news-panel').contains(document.activeElement)){
      newsIndex++;renderNews();
    }
  },8000);
  storyScene=new SolumScene($('#story-canvas'));
  const chapters={
    flood:['01 / When water finds a way.','See how flooding can connect streets, homes and essential services.'],
    landslide:['02 / When the ground gives way.','A regional hillside illustration: slope failure can cut access and affect nearby homes.'],
    cyclone:['03 / When the winds gather.','Wind, rain and service disruption can combine. Preparation starts before the storm.']
  };
  $$('[data-chapter]').forEach(b=>b.onclick=()=>{
    storyScene.setChapter(b.dataset.chapter);
    $$('[data-chapter]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b)});
    $('#story-title').textContent=chapters[b.dataset.chapter][0];
    $('#story-desc').textContent=chapters[b.dataset.chapter][1];
  });
  $('#story-play').textContent=storyScene.playing?'Ⅱ':'▶';
  $('#story-play').onclick=()=>{
    storyScene.playing=!storyScene.playing;
    $('#story-play').textContent=storyScene.playing?'Ⅱ':'▶';
    $('#story-play').setAttribute('aria-label',storyScene.playing?'Pause animation':'Play animation');
  };
}

function loadSatellite(){
  const lat=locationData.lat,lon=locationData.lon,d=.025;
  const u='https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox='+[lon-d,lat-d,lon+d,lat+d].join(',')+'&bboxSR=4326&size=1200,650&format=jpg&f=image';
  $('#satellite-error').classList.add('hidden');
  $('#satellite-image').onerror=()=>$('#satellite-error').classList.remove('hidden');
  $('#satellite-image').src=u;
  $('#map-title').textContent=locationData.name+' · Satellite Basemap';
  $('#map-subtitle').textContent='High-resolution imagery context';
}

async function loadMapOverlays(lat, lon){
  if(!googleMap)return;
  try{
    const geoData=await api(`/api/maps/overlays?lat=${lat}&lon=${lon}`);
    googleMap.data.forEach(f=>googleMap.data.remove(f));
    if(geoData?.features?.length){
      googleMap.data.addGeoJson(geoData);
    }
  }catch(err){
    console.warn('Overlays loading note:', err);
  }
}

function showMapNotice(msg, duration = 6500) {
  const b = $('#map-notice-banner');
  if (!b) return;
  b.innerHTML = msg;
  b.classList.remove('hidden');
  clearTimeout(b._timer);
  b._timer = setTimeout(() => { b.classList.add('hidden'); }, duration);
}

function hideMapNotice() {
  const b = $('#map-notice-banner');
  if (b) {
    b.classList.add('hidden');
    clearTimeout(b._timer);
  }
}

async function inspectCoordinates(lat, lon) {
  toast(`Inspecting coordinates: ${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E`);
  $('#map-title').textContent = `${locationData.name} · ${lat.toFixed(4)}°, ${lon.toFixed(4)}°`;
  try {
    const ctx = await fetch('/api/maps/location-context', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ latitude: lat, longitude: lon })
    }).then(r => r.json());
    if (ctx.elevation_m !== undefined) {
      const waterTxt = ctx.water_corridors?.[0] ? ` · Water: ${ctx.water_corridors[0].name} (${ctx.water_corridors[0].distance_m}m)` : '';
      $('#map-subtitle').textContent = `Copernicus Elevation: ${ctx.elevation_m}m AMSL · ${ctx.flood_zone}${waterTxt}`;
      if ($('#brief-coords')) $('#brief-coords').textContent = `${lat.toFixed(3)}°N, ${lon.toFixed(3)}°E`;
    }
  } catch (err) {}
}

async function loadMapMarkers(){
  try{
    if(googleMap){
      googleMapMarkers.forEach(m=>m.setMap(null));
      googleMapMarkers=[];
    }
    if(googleMap3DMarkers.length){
      googleMap3DMarkers.forEach(m=>{try{m.remove();}catch(e){}});
      googleMap3DMarkers=[];
    }
    const targetDistrict = locationData.district || locationData.name || 'Chennai';
    const issueList=await api('/api/issues?status=open&district='+encodeURIComponent(targetDistrict));
    if(!Array.isArray(issueList))return;

    const infoWindow=googleMap?new google.maps.InfoWindow():null;
    issueList.forEach(iss=>{
      if(iss.latitude&&iss.longitude){
        if(googleMap){
          const marker=new google.maps.Marker({
            position:{lat:iss.latitude,lng:iss.longitude},
            map:googleMap,
            title:`${iss.title} (${iss.status})`,
            icon:{
              path:google.maps.SymbolPath.CIRCLE,
              scale:8,
              fillColor:iss.priority==='Critical'?'#e03a3a':'#d97706',
              fillOpacity:0.95,
              strokeColor:'#ffffff',
              strokeWeight:2
            }
          });
          marker.addListener('click',()=>{
            infoWindow.setContent(`
              <div style="font-family:inherit;padding:4px 8px;max-width:240px">
                <b style="color:#112017;font-size:13px">${esc(iss.title)}</b>
                <p style="margin:4px 0;font-size:11px;color:#555">${esc(iss.place||iss.description||'')}</p>
                <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:#fef3c7;color:#92400e;font-weight:600">${esc(iss.type||iss.category||'Issue')} · ${esc(iss.status)}</span>
              </div>
            `);
            infoWindow.open(googleMap,marker);
          });
          googleMapMarkers.push(marker);
        }

        if(googleMap3D&&Marker3DElementClass){
          try{
            const m3d=new Marker3DElementClass({
              position:{lat:iss.latitude,lng:iss.longitude,altitude:30},
              altitudeMode:'RELATIVE_TO_GROUND',
              extruded:true,
              label:iss.title
            });
            m3d.addEventListener('gmp-click',()=>{
              toast(`[3D] ${iss.title} · ${iss.place||''} (${iss.status})`);
            });
            googleMap3D.append(m3d);
            googleMap3DMarkers.push(m3d);
          }catch(e){}
        }
      }
    });
  }catch(err){}
}

async function loadGoogleMaps3D(){
  if(gmpLoaded&&(googleMap3D||googleMap))return true;
  try{
    const config=await api('/api/maps/config');
    if(!config?.api_key)return false;

    if(!window.google?.maps){
      await new Promise((resolve,reject)=>{
        const script=document.createElement('script');
        script.src=`https://maps.googleapis.com/maps/api/js?key=${config.api_key}&v=alpha&libraries=maps3d,places,marker,geometry`;
        script.async=true;
        script.defer=true;
        script.onload=()=>resolve();
        script.onerror=err=>reject(err);
        document.head.appendChild(script);
      });
    }

    const wrap=$('#gmp-3d-wrap');
    if(!wrap)return false;
    wrap.style.display='block';
    $('#map-canvas').style.display='none';

    currentTilt=65;
    currentHeading=20;
    activeMapMode='3d';

    // 1. Initialize Photorealistic 3D Web Component
    try{
      if(google.maps.importLibrary){
        const maps3dLib=await google.maps.importLibrary("maps3d");
        Map3DElementClass=maps3dLib.Map3DElement;
        Marker3DElementClass=maps3dLib.Marker3DElement;
      }
      if(Map3DElementClass){
        googleMap3D=new Map3DElementClass({
          center:{lat:locationData.lat,lng:locationData.lon,altitude:35},
          tilt:65,
          heading:20,
          range:1200,
          mode:'HYBRID'
        });
        googleMap3D.addEventListener('gmp-click',async e=>{
          const lat=e.position?.lat??locationData.lat;
          const lon=e.position?.lng??locationData.lon;
          inspectCoordinates(lat,lon);
        });
        const container3d=$('#google-map-3d');
        if(container3d)container3d.replaceChildren(googleMap3D);
        map3dSupported=true;
      }else{
        map3dSupported=false;
      }
    }catch(e3d){
      console.warn('Google Maps 3D Platform WebGL/Alpha notice:', e3d);
      map3dSupported=false;
    }

    // 2. Initialize 2D Google Map (for 2D Satellite, 2D Roadmap & Water Bodies)
    const mapContainer=$('#google-map');
    if(mapContainer){
      googleMap=new google.maps.Map(mapContainer,{
        center:{lat:locationData.lat,lng:locationData.lon},
        zoom:16,
        tilt:0,
        heading:0,
        mapTypeId:'satellite',
        disableDefaultUI:true,
        gestureHandling:'greedy'
      });

      googleMap.data.setStyle(feature=>{
        const ftype=feature.getProperty('type');
        const waterVisible=$('#layer-water')?.checked??true;
        const floodVisible=$('#layer-flood')?.checked??true;
        const issuesVisible=$('#layer-issues')?.checked??true;

        if(ftype==='scenario_hazard_zone'){
          return {
            fillColor: feature.getProperty('fill_color') || '#ef4444',
            fillOpacity: feature.getProperty('fill_opacity') || 0.42,
            strokeColor: feature.getProperty('stroke_color') || '#b91c1c',
            strokeWeight: feature.getProperty('stroke_weight') || 2.5,
            visible: floodVisible,
            zIndex: 15
          };
        }
        if(ftype==='scenario_road'){
          return {
            strokeColor: feature.getProperty('stroke_color') || '#ef4444',
            strokeWeight: feature.getProperty('stroke_weight') || 4,
            strokeOpacity: feature.getProperty('stroke_opacity') || 0.9,
            visible: floodVisible,
            zIndex: 25
          };
        }
        if(ftype==='scenario_facility'){
          return {
            icon: {
              path: google.maps.SymbolPath.CIRCLE,
              scale: 6.5,
              fillColor: feature.getProperty('marker_color') || '#dc2626',
              fillOpacity: 0.95,
              strokeColor: '#ffffff',
              strokeWeight: 2
            },
            visible: issuesVisible,
            zIndex: 30
          };
        }

        if(ftype==='River Line'||feature.getGeometry().getType()==='LineString'){
          return {
            strokeColor:'#0284c7',
            strokeWeight:3.5,
            strokeOpacity:0.85,
            visible:waterVisible
          };
        }
        if(ftype==='Statutory Buffer'||feature.getProperty('buffer')){
          return {
            fillColor:'#f59e0b',
            fillOpacity:0.25,
            strokeColor:'#d97706',
            strokeWeight:1.5,
            visible:floodVisible
          };
        }
        return {
          fillColor:'#0ea5e9',
          fillOpacity:0.42,
          strokeColor:'#0284c7',
          strokeWeight:2,
          visible:waterVisible
        };
      });

      const overlayInfo=new google.maps.InfoWindow();
      googleMap.data.addListener('click',event=>{
        const f=event.feature;
        const ftype=f.getProperty('type');
        if(ftype==='scenario_hazard_zone'||ftype==='scenario_road'||ftype==='scenario_facility'){
          const title=f.getProperty('title')||f.getProperty('name')||'Scenario Element';
          const desc=f.getProperty('desc')||f.getProperty('details')||'';
          const sev=f.getProperty('severity')||f.getProperty('status')||'';
          overlayInfo.setContent(`
            <div style="font-family:inherit;padding:4px 8px;max-width:250px">
              <b style="color:#b91c1c;font-size:13px">${esc(title)}</b>
              <p style="margin:4px 0;font-size:11px;color:#333">${esc(desc)}</p>
              ${sev?`<span style="font-size:10px;padding:2px 6px;border-radius:4px;background:#fee2e2;color:#991b1b;font-weight:600">${esc(String(sev).toUpperCase())}</span>`:''}
            </div>
          `);
          overlayInfo.setPosition(event.latLng);
          overlayInfo.open(googleMap);
          return;
        }

        const name=f.getProperty('name')||'Water Body';
        const type=f.getProperty('type')||'Water Feature';
        const basin=f.getProperty('basin')||'Tamil Nadu Basin';
        overlayInfo.setContent(`
          <div style="font-family:inherit;padding:4px 8px;max-width:240px">
            <b style="color:#0284c7;font-size:13px">${esc(name)}</b>
            <p style="margin:4px 0;font-size:11px;color:#444">Type: ${esc(type)}<br>Basin: ${esc(basin)}</p>
            <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:#e0f2fe;color:#0369a1;font-weight:600">Verified India-WRIS / PWD</span>
          </div>
        `);
        overlayInfo.setPosition(event.latLng);
        overlayInfo.open(googleMap);
      });

      googleMap.addListener('click',async e=>{
        inspectCoordinates(e.latLng.lat(),e.latLng.lng());
      });
    }

    await loadMapOverlays(locationData.lat, locationData.lon);
    await loadMapMarkers();

    $('#layer-water')?.addEventListener('change',()=>googleMap?.data.setStyle(googleMap.data.getStyle()));
    $('#layer-flood')?.addEventListener('change',()=>googleMap?.data.setStyle(googleMap.data.getStyle()));
    $('#layer-tilt')?.addEventListener('change',e=>{
      if(activeMapMode==='3d'&&googleMap3D){
        googleMap3D.tilt=e.target.checked?67.5:0;
      }else if(googleMap){
        currentTilt=e.target.checked?45:0;
        googleMap.setTilt(currentTilt);
      }
    });
    $('#layer-issues')?.addEventListener('change',e=>{
      const vis=e.target.checked;
      googleMapMarkers.forEach(m=>m.setVisible(vis));
      googleMap3DMarkers.forEach(m=>{m.style.display=vis?'block':'none';});
    });

    gmpLoaded=true;

    if(map3dSupported&&googleMap3D){
      $('#google-map-3d').style.display='block';
      if(mapContainer)mapContainer.style.display='none';
      $('#map-title').textContent=`${locationData.name} · Photorealistic 3D`;
      $('#map-subtitle').textContent='Google Maps 3D Platform · True 3D terrain & photorealistic aerial mesh';
      $('#map-mode-indicator').textContent='Photorealistic 3D';
    }else{
      if(mapContainer)mapContainer.style.display='block';
      $('#google-map-3d').style.display='none';
      if(googleMap){
        googleMap.setMapTypeId('hybrid');
        googleMap.setTilt(45);
      }
      $('#map-title').textContent=`${locationData.name} · Satellite 3D Perspective (Fallback)`;
      $('#map-subtitle').textContent='High-resolution Google Earth imagery with 45° perspective camera';
      $('#map-mode-indicator').textContent='Satellite 3D (Fallback)';
      showMapNotice('Photorealistic 3D WebGL element unavailable on this browser/GPU; high-resolution satellite perspective active.',6000);
    }
    return true;
  }catch(err){
    console.warn('Google Maps 3D loading note (fallback active):', err);
    $('#gmp-3d-wrap').style.display='none';
    $('#map-canvas').style.display='block';
    return false;
  }
}

async function initSimulation(scenarioType='auto'){
  try{
    const reqBody = {
      district: locationData.district || 'Chennai',
      city: locationData.city || locationData.name || 'Velachery',
      latitude: locationData.lat,
      longitude: locationData.lon,
      lat: locationData.lat,
      lon: locationData.lon,
      location_name: locationData.name || 'Velachery',
      scenario_type: scenarioType
    };
    const res = await fetch('/api/simulation/create', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(reqBody)
    });
    if(!res.ok) throw new Error('Simulation init failed');
    simMeta = await res.json();
    simCache = {};
    simHour = 0;

    const simId = simMeta.simulation_id || simMeta.id;
    const simTitle = simMeta.scenario_title || simMeta.title || 'Environmental Scenario';

    // Render scenario selector pills
    const pillsWrap = $('#scenario-pills');
    if(pillsWrap && simMeta.supported_scenarios){
      pillsWrap.innerHTML = simMeta.supported_scenarios.map(sc => {
        const scType = typeof sc === 'object' ? sc.type : sc;
        const rawTitle = typeof sc === 'object' ? sc.title : sc;
        const iconEmoji = scType.includes('landslide') ? '⛰️' : scType.includes('cyclone') ? '🌀' : '🌊';
        const displayLabel = scType.charAt(0).toUpperCase() + scType.slice(1);
        return `
          <button type="button" class="scenario-pill-btn ${scType === simMeta.scenario_type ? 'active' : ''}" data-scenario="${scType}">
            ${esc(displayLabel)} ${iconEmoji}
          </button>
        `;
      }).join('');

      $$('.scenario-pill-btn').forEach(btn => {
        btn.onclick = () => {
          const stype = btn.dataset.scenario;
          if(stype !== simMeta.scenario_type){
            if(simPlaying) toggleSimulationPlay();
            initSimulation(stype);
          }
        };
      });
    }

    const badge = $('#scenario-badge');
    if(badge) badge.textContent = simTitle;
    const label = $('#scenario-label');
    if(label) label.textContent = `Simulation +0 h · Baseline`;

    const slider = $('#scenario-time');
    if(slider) slider.value = 0;

    await applySimulationHour(0);
  }catch(err){
    console.warn('Simulation initialization notice:', err);
  }
}

async function applySimulationHour(hour){
  simHour = hour;
  const slider = $('#scenario-time');
  if(slider && Number(slider.value) !== hour) slider.value = hour;

  const label = $('#scenario-label');
  if(label){
    label.textContent = `Simulation +${hour} h · ${hour === 0 ? 'Baseline' : hour >= 18 ? 'Peak Hazard' : 'Evolving'}`;
  }

  if(mapScene) mapScene.setLevel(0.08 + (hour / 24) * 0.92);

  const simId = simMeta?.simulation_id || simMeta?.id;
  if(!simId) return;

  try{
    let state = simCache[hour];
    if(!state){
      const res = await fetch(`/api/simulation/${simId}/state?hour=${hour}`);
      if(res.ok){
        state = await res.json();
        simCache[hour] = state;
      }
    }

    if(!state) return;

    const card = $('#scenario-detail-card');
    if(card) card.style.display = 'block';

    const stageTitle = $('#sim-stage-title');
    if(stageTitle){
      stageTitle.textContent = `${state.stage_label || state.stage_title || 'Simulation Stage'} (+${hour} Hours)`;
    }

    const stageDesc = $('#sim-stage-desc');
    if(stageDesc){
      stageDesc.textContent = state.narrative || state.stage_description || '';
    }

    const mGrid = $('#sim-metrics-grid');
    if(mGrid && state.metrics){
      const m = state.metrics;
      mGrid.innerHTML = `
        <div class="sim-metric-item">
          <div class="sim-metric-val">${m.inundation_depth_cm ?? 0} cm</div>
          <div class="sim-metric-lbl">Inundation Depth</div>
        </div>
        <div class="sim-metric-item">
          <div class="sim-metric-val">${m.rainfall_accumulated_mm ?? 0} mm</div>
          <div class="sim-metric-lbl">Rainfall Total</div>
        </div>
        <div class="sim-metric-item">
          <div class="sim-metric-val">${m.peak_wind_gust_kmh ?? 0} km/h</div>
          <div class="sim-metric-lbl">Peak Gust</div>
        </div>
        <div class="sim-metric-item">
          <div class="sim-metric-val">${m.affected_area_sqkm ?? 0} km²</div>
          <div class="sim-metric-lbl">Affected Area</div>
        </div>
        <div class="sim-metric-item">
          <div class="sim-metric-val">${((m.water_accumulation_volume_m3 || 0) / 1000).toFixed(0)}k m³</div>
          <div class="sim-metric-lbl">Runoff Volume</div>
        </div>
        <div class="sim-metric-item">
          <div class="sim-metric-val">${m.soil_saturation_pct ?? m.soil_moisture_saturation_pct ?? 0}%</div>
          <div class="sim-metric-lbl">Soil Saturation</div>
        </div>
      `;
    }

    const roadsList = $('#sim-roads-list');
    const roadItems = state.roads_affected || state.affected_infrastructure?.roads || [];
    if(roadsList && roadItems.length){
      roadsList.innerHTML = roadItems.map(r => `
        <li class="sim-road-item">
          <div class="sim-road-info">
            <span class="sim-road-name">${esc(r.name)}</span>
            <span class="sim-road-meta">${esc(r.impact || r.condition || '')} · ${esc(r.action || '')}</span>
          </div>
          <span class="sim-badge ${String(r.status).toLowerCase().includes('barricaded') || String(r.status).toLowerCase().includes('waterlogging') ? 'closed' : 'passable'}">${esc(r.status)}</span>
        </li>
      `).join('');
    }

    const facList = $('#sim-facilities-list');
    const facilityItems = state.critical_facilities || state.affected_infrastructure?.critical_facilities || [];
    if(facList && facilityItems.length){
      facList.innerHTML = facilityItems.map(f => `
        <li class="sim-facility-item">
          <div class="sim-facility-info">
            <span class="sim-facility-name">${esc(f.name)}</span>
            <span class="sim-facility-meta">${esc(f.type || f.category || 'Facility')}</span>
          </div>
          <span class="sim-badge ${String(f.status).toLowerCase().includes('isolation') || String(f.status).toLowerCase().includes('diverted') ? 'offline' : 'nominal'}">${esc(f.status)}</span>
        </li>
      `).join('');
    }

    const groundNote = $('#sim-grounding-note');
    if(groundNote){
      const assumptionsText = (state.model_assumptions || []).join(' ');
      const sourcesText = (state.data_sources || []).join('; ');
      groundNote.textContent = state.grounding_note || (assumptionsText ? `${assumptionsText} Grounded in: ${sourcesText}` : 'Modeled scenario for civic preparedness.');
    }

    if(googleMap && state.geojson){
      simGeoJsonFeatures.forEach(f => googleMap.data.remove(f));
      simGeoJsonFeatures = [];
      const added = googleMap.data.addGeoJson(state.geojson);
      if(Array.isArray(added)) simGeoJsonFeatures = added;
    }

    if(googleMap3D){
      sim3DMarkers.forEach(m => {
        try{ m.remove(); }catch(e){}
      });
      sim3DMarkers = [];

      if(Marker3DElementClass && state.geojson && state.geojson.features){
        state.geojson.features.forEach(feat => {
          if(feat.geometry && feat.geometry.type === 'Point'){
            const coords = feat.geometry.coordinates;
            try{
              const m3d = new Marker3DElementClass({
                position: { lat: coords[1], lng: coords[0], altitude: 12 },
                title: feat.properties.title || feat.properties.name || 'Scenario Marker',
                extruded: true,
                altitudeMode: 'RELATIVE_TO_GROUND'
              });
              googleMap3D.append(m3d);
              sim3DMarkers.push(m3d);
            }catch(e){}
          }
        });
      }
    }

  }catch(err){
    console.warn('Simulation hour update notice:', err);
  }
}

function toggleSimulationPlay(){
  if(simPlaying){
    clearInterval(simTimer);
    simTimer = null;
    simPlaying = false;
    const btn = $('#map-motion');
    if(btn){
      btn.textContent = '▶';
      btn.setAttribute('aria-label', 'Play simulation timeline');
    }
    if(mapScene) mapScene.playing = false;
    toast('Simulation playback paused.');
  }else{
    simPlaying = true;
    const btn = $('#map-motion');
    if(btn){
      btn.textContent = 'Ⅱ';
      btn.setAttribute('aria-label', 'Pause simulation timeline');
    }
    if(mapScene) mapScene.playing = true;
    toast('Playing 24h simulation scenario…');

    simTimer = setInterval(() => {
      let nextH = simHour + 6;
      if(nextH > 24) nextH = 0;
      applySimulationHour(nextH);
    }, 3200);
  }
}

function resetSimulation(){
  if(simPlaying) toggleSimulationPlay();
  applySimulationHour(0);
  toast('Scenario reset to Baseline (0h).');
}

function initPrepare(){
  mapScene=new SolumScene($('#map-canvas'));
  loadGoogleMaps3D();

  $$('[data-map-mode]').forEach(b=>b.onclick=()=>{
    const m=b.dataset.mapMode;
    const prevMode=activeMapMode;
    activeMapMode=m;
    $$('[data-map-mode]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',x===b)});

    if(isOrbiting&&googleMap3D){
      try{googleMap3D.stopCameraAnimation();}catch(e){}
      isOrbiting=false;
    }

    if(googleMap||googleMap3D){
      $('#gmp-3d-wrap').style.display='block';
      $('#map-canvas').style.display='none';
      $('#satellite-layer').style.display='none';
      $('.map-legend').style.display='flex';
      $('.map-zoom').style.display='grid';

      if(m==='3d'){
        if(map3dSupported&&googleMap3D){
          $('#google-map-3d').style.display='block';
          $('#google-map').style.display='none';
          try{
            googleMap3D.flyCameraTo({
              endCamera:{
                center:{lat:locationData.lat,lng:locationData.lon,altitude:35},
                tilt:65,
                heading:20,
                range:1200
              },
              durationMillis:1800
            });
          }catch(e){}
          $('#map-title').textContent=`${locationData.name} · Photorealistic 3D`;
          $('#map-subtitle').textContent='Google Maps 3D Platform · Photorealistic 3D terrain & buildings';
          $('#map-mode-indicator').textContent='Photorealistic 3D';
          hideMapNotice();
          toast('Photorealistic 3D active: 3D terrain with pitch, orbit & camera controls.');
        }else{
          $('#google-map-3d').style.display='none';
          $('#google-map').style.display='block';
          if(googleMap){
            googleMap.setMapTypeId('hybrid');
            googleMap.setTilt(45);
          }
          $('#map-title').textContent=`${locationData.name} · Satellite 3D Perspective (Fallback)`;
          $('#map-subtitle').textContent='High-resolution Google Earth imagery with 45° perspective camera';
          $('#map-mode-indicator').textContent='Satellite 3D (Fallback)';
          showMapNotice('Photorealistic 3D WebGL element unavailable on this browser/GPU; high-resolution satellite perspective active.',6000);
        }
      }else if(m==='satellite'){
        $('#google-map-3d').style.display='none';
        $('#google-map').style.display='block';
        if(googleMap){
          googleMap.setMapTypeId('satellite');
          googleMap.setTilt(0);
          currentTilt=0;
        }
        $('#map-title').textContent=`${locationData.name} · 2D Satellite Basemap`;
        $('#map-subtitle').textContent='High-resolution nadir aerial photography from Google Earth';
        $('#map-mode-indicator').textContent='True Satellite';
        if(prevMode==='3d'){
          showMapNotice('Switched to 2D Satellite Basemap. Note: Photorealistic 3D is a separate interactive mode featuring 3D elevation, pitch, and orbit controls. Select "3D view" anytime for 3D perspective.',7500);
          toast('Switched to 2D Satellite Basemap.');
        }else{
          hideMapNotice();
        }
      }else if(m==='2d'){
        $('#google-map-3d').style.display='none';
        $('#google-map').style.display='block';
        if(googleMap){
          googleMap.setMapTypeId('roadmap');
          googleMap.setTilt(0);
          currentTilt=0;
        }
        $('#map-title').textContent=`${locationData.name} · 2D Civic Plan`;
        $('#map-subtitle').textContent='Standard cartographic view with road networks & locality boundaries';
        $('#map-mode-indicator').textContent='2D Civic Plan';
        hideMapNotice();
      }else if(m==='water'){
        $('#google-map-3d').style.display='none';
        $('#google-map').style.display='block';
        if(googleMap){
          googleMap.setMapTypeId('hybrid');
          googleMap.setTilt(25);
          currentTilt=25;
        }
        $('#map-title').textContent=`${locationData.name} · Water Bodies & Corridors`;
        $('#map-subtitle').textContent='Verified India-WRIS / PWD water bodies, river corridors & 100m catchment buffers';
        $('#map-mode-indicator').textContent='Water Bodies & Catchments';
        hideMapNotice();
      }
    }else{
      if(m==='satellite'){
        $('#gmp-3d-wrap').style.display='none';
        $('#map-canvas').style.display='none';
        $('#satellite-layer').style.display='block';
        $('.map-legend').style.display='none';
        $('.map-zoom').style.display='none';
        $('#map-mode-indicator').textContent='Satellite Basemap';
        loadSatellite();
      }else{
        $('#gmp-3d-wrap').style.display='none';
        $('#map-canvas').style.display='block';
        $('#satellite-layer').style.display='none';
        $('.map-legend').style.display='flex';
        $('.map-zoom').style.display='grid';
        mapScene.setMode(m);
        $('#map-title').textContent=`${locationData.name} · ${m==='2d'?'2D Plan':'Water Corridor'}`;
        $('#map-subtitle').textContent=m==='2d'?'Schematic plan view':'Hydrological corridors and catchment zones';
        $('#map-mode-indicator').textContent=m.toUpperCase();
      }
    }
  });

  $$('[data-zoom]').forEach(b=>b.onclick=()=>{
    const action=b.dataset.zoom;
    if(activeMapMode==='3d'&&googleMap3D&&map3dSupported){
      if(action==='in'){
        googleMap3D.range=Math.max(150,(googleMap3D.range||1200)*0.7);
        toast(`3D altitude range: ${Math.round(googleMap3D.range)}m`);
      }else if(action==='out'){
        googleMap3D.range=Math.min(30000,(googleMap3D.range||1200)*1.4);
        toast(`3D altitude range: ${Math.round(googleMap3D.range)}m`);
      }else if(action==='tilt'){
        const curTilt=googleMap3D.tilt||0;
        googleMap3D.tilt=curTilt>35?0:67.5;
        if($('#layer-tilt'))$('#layer-tilt').checked=(googleMap3D.tilt>0);
        toast(`3D camera tilt: ${Math.round(googleMap3D.tilt)}°`);
      }else if(action==='rotate'){
        googleMap3D.heading=((googleMap3D.heading||0)+45)%360;
        toast(`Camera heading: ${Math.round(googleMap3D.heading)}°`);
      }else if(action==='orbit'){
        if(isOrbiting){
          try{googleMap3D.stopCameraAnimation();}catch(e){}
          isOrbiting=false;
          toast('360° Cinematic Orbit paused.');
        }else{
          isOrbiting=true;
          toast('360° Cinematic Orbit active…');
          try{
            googleMap3D.flyCameraAround({
              camera:{
                center:{lat:locationData.lat,lng:locationData.lon,altitude:35},
                tilt:65,
                range:googleMap3D.range||1200
              },
              durationMillis:18000,
              repeatCount:1
            });
          }catch(e){}
        }
      }else if(action==='reset'){
        if(isOrbiting){
          try{googleMap3D.stopCameraAnimation();}catch(e){}
          isOrbiting=false;
        }
        try{
          googleMap3D.flyCameraTo({
            endCamera:{
              center:{lat:locationData.lat,lng:locationData.lon,altitude:35},
              tilt:65,
              heading:20,
              range:1200
            },
            durationMillis:1500
          });
        }catch(e){}
        if($('#layer-tilt'))$('#layer-tilt').checked=true;
        toast('Camera reset to angled 3D view (tilt 65°, range 1200m).');
      }
    }else if(googleMap&&$('#gmp-3d-wrap').style.display==='block'){
      if(action==='in'){
        googleMap.setZoom(googleMap.getZoom()+1);
      }else if(action==='out'){
        googleMap.setZoom(googleMap.getZoom()-1);
      }else if(action==='tilt'){
        currentTilt=currentTilt>30?0:45;
        googleMap.setTilt(currentTilt);
        if($('#layer-tilt'))$('#layer-tilt').checked=(currentTilt>0);
        toast(`3D camera tilt: ${currentTilt}°`);
      }else if(action==='rotate'||action==='orbit'){
        currentHeading=(currentHeading+45)%360;
        googleMap.setHeading(currentHeading);
        toast(`Camera heading: ${currentHeading}°`);
      }else if(action==='reset'){
        currentHeading=0;
        currentTilt=0;
        googleMap.setHeading(0);
        googleMap.setTilt(0);
        googleMap.setZoom(16);
        googleMap.panTo({lat:locationData.lat,lng:locationData.lon});
        if($('#layer-tilt'))$('#layer-tilt').checked=false;
        toast('Camera view reset to origin.');
      }
    }else{
      if(action==='reset'){
        mapScene.zoom=1;mapScene.angle=0;
      }else if(action==='tilt'||action==='rotate'||action==='orbit'){
        mapScene.angle=(mapScene.angle||0)+Math.PI/6;
      }else{
        mapScene.zoom=Math.max(.65,Math.min(1.8,mapScene.zoom+(action==='in'?.15:-.15)));
      }
      mapScene.draw();
    }
  });

  const simSlider=$('#scenario-time');
  if(simSlider){
    simSlider.oninput=e=>{
      applySimulationHour(Number(e.target.value));
    };
  }

  const motionBtn=$('#map-motion');
  if(motionBtn){
    motionBtn.textContent=simPlaying?'Ⅱ':'▶';
    motionBtn.onclick=()=>toggleSimulationPlay();
  }

  const resetBtn=$('#scenario-reset');
  if(resetBtn){
    resetBtn.onclick=()=>resetSimulation();
  }

  // Initialize simulation engine for active location
  initSimulation('auto');

  const checked=store.get('checklist',{});
  $$('[data-check]').forEach(c=>{
    c.checked=!!checked[c.dataset.check];
    c.onchange=()=>{
      checked[c.dataset.check]=c.checked;
      store.set('checklist',checked);
    };
  });

  $('#chat-form').onsubmit=e=>{
    e.preventDefault();
    sendSolumAiMessage($('#chat-input').value, true);
  };
  $$('[data-question]').forEach(b=>b.onclick=()=>sendSolumAiMessage(b.dataset.question, true));
}

function renderMarkdown(md){
  if(!md)return '';
  let s=esc(md);
  s=s.replace(/\*\*(.*?)\*\*/g,'<b>$1</b>');
  s=s.replace(/^\s*[-•]\s+(.*)$/gm,'<li>$1</li>');
  s=s.replace(/(<li>.*<\/li>)/s,'<ul style="margin:6px 0;padding-left:18px">$1</ul>');
  s=s.replace(/\n\n/g,'<br><br>').replace(/\n/g,'<br>');
  return s;
}

async function sendSolumAiMessage(q, inPageChat=false){
  q=String(q||'').trim();
  if(!q)return;

  const targetBody=inPageChat?$('#chat-log'):$('#solum-ai-body');
  if(!inPageChat){
    const panel=$('#solum-ai-panel');
    if(panel&&panel.classList.contains('hidden')){
      panel.classList.remove('hidden');
      solumAiOpen=true;
    }
  }

  if(targetBody){
    const userMsg=document.createElement('div');
    userMsg.className=inPageChat?'bubble user':'solum-ai-msg user';
    userMsg.textContent=q;
    targetBody.append(userMsg);
    targetBody.scrollTop=targetBody.scrollHeight;
  }

  if($('#solum-ai-input'))$('#solum-ai-input').value='';
  if($('#chat-input'))$('#chat-input').value='';

  let typingEl=null;
  if(targetBody){
    typingEl=document.createElement('div');
    typingEl.className=inPageChat?'bubble':'solum-ai-typing';
    typingEl.innerHTML=inPageChat?'Consulting SOLUM AI engine…':'<span class="solum-ai-dot"></span><span class="solum-ai-dot"></span><span class="solum-ai-dot"></span>';
    targetBody.append(typingEl);
    targetBody.scrollTop=targetBody.scrollHeight;
  }

  try{
    const payload={
      message:q,
      history:chatHistory.slice(-8),
      location:{
        name:locationData.name,
        district:locationData.district||locationData.name,
        state:locationData.state||'Tamil Nadu',
        lat:locationData.lat,
        lon:locationData.lon
      },
      context:{
        current_page:page,
        last_assessment:store.get('last_assessment',null)
      }
    };

    const res=await fetch('/api/chat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)
    });
    if(!res.ok)throw new Error('Chat service offline');
    const data=await res.json();

    if(typingEl)typingEl.remove();

    chatHistory.push({role:'user',content:q});
    chatHistory.push({role:'assistant',content:data.reply});

    if(targetBody){
      const botMsg=document.createElement('div');
      botMsg.className=inPageChat?'bubble':'solum-ai-msg bot';
      botMsg.innerHTML=renderMarkdown(data.reply);

      if(data.source_url){
        const src=document.createElement('div');
        src.className='solum-ai-source-tag';
        src.innerHTML=`Official reference: <a href="${esc(data.source_url)}" target="_blank" rel="noopener">${esc(data.source_title||'Government Source')} ↗</a>`;
        botMsg.append(src);
      }

      if(data.actions&&data.actions.length){
        const actWrap=document.createElement('div');
        actWrap.className='solum-ai-actions';
        data.actions.forEach(a=>{
          const btn=document.createElement('button');
          btn.type='button';
          btn.className='solum-ai-action-btn';
          btn.textContent=a.label;
          btn.onclick=()=>{
            if(a.action==='navigate'&&a.target){
              window.location.href=a.target;
            }else if(a.action==='open_dialog'){
              if(a.target==='complaint'){
                $('#complaint-form-wrap')?.classList.remove('hidden');
                $('#complaint-success')?.classList.add('hidden');
                if($('#complaint-place'))$('#complaint-place').value=formatLocationDisplay(locationData);
                $('#complaint-dialog')?.showModal();
              }else if(a.target==='location'){
                $('#location-dialog')?.showModal();
              }else if(a.target==='sources'){
                $('#sources-dialog')?.showModal();
              }
            }else if(a.action==='query'){
              sendSolumAiMessage(a.target||a.label,inPageChat);
            }
          };
          actWrap.append(btn);
        });
        botMsg.append(actWrap);
      }
      targetBody.append(botMsg);
      targetBody.scrollTop=targetBody.scrollHeight;
    }
  }catch(err){
    if(typingEl)typingEl.remove();
    let fallbackText='I can provide guidance on emergency supplies, flood buffer rules (100m catchment buffer), terrain elevation, reporting civic complaints, or 3D scenario simulations. Please check current official IMD/NDMA bulletins.';
    if(targetBody){
      const botMsg=document.createElement('div');
      botMsg.className=inPageChat?'bubble':'solum-ai-msg bot';
      botMsg.textContent=fallbackText;
      targetBody.append(botMsg);
      targetBody.scrollTop=targetBody.scrollHeight;
    }
  }
}

function askGuide(q){
  sendSolumAiMessage(q, true);
}

async function loadIssues(){
  try{
    const targetDistrict = locationData.district || locationData.name || 'Chennai';
    const targetLocality = locationData.locality || '';
    const params = new URLSearchParams({ district: targetDistrict });
    if(targetLocality) params.append('locality', targetLocality);
    const data = await api('/api/issues?' + params.toString());
    if(Array.isArray(data)){
      issues = data;
    }
  }catch(e){
    console.warn('Could not fetch location-filtered issues:', e);
    issues = [];
  }
}

async function renderResolve(){
  $('#resolve-stats').innerHTML = '<div class="metric"><span>Loading records…</span><b>…</b><span>Synchronizing</span></div>';
  await loadIssues();

  let stats = {
    total: issues.length,
    in_progress: issues.filter(i=>i.status==='In progress').length,
    resolved: issues.filter(i=>i.status==='Resolved').length,
    awaiting: issues.filter(i=>!['Resolved','In progress'].includes(i.status)).length
  };

  try{
    const targetDistrict = locationData.district || locationData.name || 'Chennai';
    const apiStats = await api('/api/issues/stats?district=' + encodeURIComponent(targetDistrict));
    if(apiStats) stats = apiStats;
  }catch(e){}

  $('#resolve-stats').innerHTML=[
    ['Reported issues', stats.total],
    ['In progress', stats.in_progress],
    ['Resolved', stats.resolved],
    ['Awaiting next step', stats.awaiting]
  ].map(a=>`<div class="metric"><span>${a[0]}</span><b>${a[1].toString().padStart(2,'0')}</b><span>${esc(locationData.name)} area</span></div>`).join('');

  const f = $('#issue-filter')?.value || 'all';
  const filtered = issues.filter(i => f === 'all' || (f === 'open' && i.status !== 'Resolved') || i.status === f || i.type === f);

  if(!filtered.some(i => i.id === selectedIssue)){
    selectedIssue = filtered[0]?.id;
  }

  if(!filtered.length){
    $('#issue-list').innerHTML = `
      <div class="card" style="text-align:center;padding:32px 18px">
        <div class="feature-icon" style="margin:0 auto 12px;background:#eef6f0;color:#0f7a37">${icon('check')}</div>
        <h3 style="font-size:16px;margin-bottom:6px">No reported issues are currently available for this location.</h3>
        <p style="font-size:12px;color:#64766b;margin:0 auto 16px;max-width:380px">There are zero active disruptions recorded in ${esc(locationData.name)}, ${esc(locationData.district || 'Tamil Nadu')}. You can log a new civic observation below.</p>
        <button class="btn-soft" data-action="complaint" style="font-size:12px;padding:8px 16px">Raise a Complaint ${icon('arrow')}</button>
      </div>
    `;
    $('#issue-detail').innerHTML = `
      <div class="card" style="text-align:center;padding:40px 18px">
        <span class="eyebrow plain">LOCATION CLEAR</span>
        <h3 style="margin-top:10px">All clear in ${esc(locationData.name)}</h3>
        <p style="font-size:13px;color:#64766b">Selected geographical scope: <b>${esc(locationData.district || locationData.name)}, Tamil Nadu</b></p>
        <p style="font-size:12px;color:#888">Verified datasets from India-WRIS and municipal registries confirm normal status.</p>
      </div>
    `;
  } else {
    $('#issue-list').innerHTML = filtered.map(i=>`
      <button class="issue-card ${i.id === selectedIssue ? 'active' : ''}" data-issue="${esc(i.id)}" aria-pressed="${i.id === selectedIssue}">
        <span class="feature-icon">${icon(i.icon)}</span>
        <span class="issue-main">
          <h3>${esc(i.title)}</h3>
          <p>${esc(i.place)} · <small style="color:#0f7a37;font-weight:600">${esc(i.locality || i.district || '')}</small></p>
          <span class="row-flex">
            ${badge(i.priority, i.priority === 'Critical' ? 'red' : i.priority === 'High' ? 'amber' : 'gray')}
            ${badge(i.status, i.status === 'Resolved' ? '' : 'gray')}
            ${badge(i.record_type === 'demonstration' ? 'DEMO' : 'CITIZEN', 'gray')}
          </span>
        </span>
        <span class="issue-chevron">→</span>
      </button>
    `).join('');
    $$('[data-issue]').forEach(b=>b.onclick=()=>{selectedIssue=b.dataset.issue;renderResolve()});
    renderIssueDetail();
  }
}

function renderIssueDetail(){
  const i = issues.find(x => x.id === selectedIssue);
  if(!i){
    $('#issue-detail').innerHTML = '<div class="card"><p>Select an issue to inspect details.</p></div>';
    return;
  }
  const isDemo = (i.record_type === 'demonstration');
  $('#issue-detail').innerHTML = `
    <div class="row-flex between">
      <span class="row-flex" style="gap:6px">
        ${badge(i.status, i.status === 'Resolved' ? '' : 'amber')}
        ${badge(isDemo ? 'DEMONSTRATION RECORD' : 'CITIZEN REPORT', isDemo ? 'gray' : 'amber')}
      </span>
      <span class="small muted">${esc(i.id)}</span>
    </div>
    <h2 style="margin-top:12px">${esc(i.title)}</h2>
    <p style="font-size:12px">${icon('pin')} ${esc(i.place)} <span class="tag gray">${esc(i.locality || i.district || '')}</span></p>
    <div class="row-flex between small"><b>Repair progress</b><b>${i.progress}%</b></div>
    <div class="progress-track"><span style="width:${i.progress}%"></span></div>
    <p style="font-size:13px">${esc(i.update)}</p>
    <div class="details-grid">
      <div><small>RESPONSIBLE TEAM</small><b>${esc(i.owner)}</b></div>
      <div><small>WORK DURATION</small><b>${i.hours ? i.hours + ' hours' : 'Not assessed'}</b></div>
      <div><small>CREW ALLOCATION</small><b>${i.crew ? i.crew + ' people' : 'Not assigned'}</b></div>
      <div><small>DATA SOURCE</small><b style="font-size:11px">${esc(i.data_source || (i.local ? 'Citizen complaint' : 'Demonstration record'))}</b></div>
    </div>
    <ol class="steps">${i.steps.map((s,n)=>`<li class="${n > Math.floor(i.progress / 30) ? 'pending' : ''}"><b>${esc(s)}</b><small>${n === 0 ? 'Recorded in database' : n > Math.floor(i.progress / 30) ? 'Pending work step' : 'Milestone completed'}</small></li>`).join('')}</ol>
    <div class="subtle">${icon('alert')} ${esc(i.risk)}</div>
    ${i.evidence?.length ? `<p class="source-line">Uploaded evidence: ${i.evidence.map(esc).join(', ')}</p>` : ''}
    <p class="source-line">${isDemo ? 'Demonstration scenario data · Not an official municipal notification' : 'Recorded in persistent SQLite database · Citizen submission'}</p>
  `;
}

let evidenceURLs=[];
$('#complaint-evidence').onchange=e=>{
  evidenceURLs.forEach(URL.revokeObjectURL);
  evidenceURLs=[];
  $('#media-preview').replaceChildren();
  const files=[...e.target.files];
  if(files.length>3||files.some(f=>f.size>10*1024*1024||!/^image\/|^video\//.test(f.type))){
    toast('Choose up to 3 image/video files, each under 10 MB.');
    e.target.value='';
    return;
  }
  files.forEach(f=>{
    const el=document.createElement(f.type.startsWith('video/')?'video':'img');
    el.src=URL.createObjectURL(f);
    evidenceURLs.push(el.src);
    el.alt=f.name;
    if(el.tagName==='VIDEO')el.controls=true;
    $('#media-preview').append(el);
  });
};

$('#complaint-form').onsubmit=async e=>{
  e.preventDefault();
  const subject=$('#complaint-subject').value.trim();
  const category=$('#complaint-category').value;
  const place=$('#complaint-place').value.trim();
  const description=$('#complaint-description').value.trim();

  if(!subject||!place||description.length<10){
    toast('Enter a subject, location and at least 10 characters of description.');
    return;
  }

  const formData=new FormData();
  formData.append('subject',subject);
  formData.append('category',category);
  formData.append('place',place);
  formData.append('description',description);
  formData.append('latitude',locationData.lat);
  formData.append('longitude',locationData.lon);
  if(locationData.district) formData.append('district', locationData.district);
  if(locationData.locality) formData.append('locality', locationData.locality);

  const fileInput=$('#complaint-evidence');
  if(fileInput.files.length){
    for(let i=0;i<Math.min(3,fileInput.files.length);i++){
      formData.append('evidence',fileInput.files[i]);
    }
  }

  toast('Submitting complaint to SOLUM database…');
  try{
    const res=await fetch('/api/issues',{
      method:'POST',
      body:formData
    });
    if(!res.ok)throw new Error('Server submission error');
    const created=await res.json();
    issues.unshift(created);
    store.set('issues',issues);
    selectedIssue=created.id;

    $('#complaint-form-wrap').classList.add('hidden');
    $('#complaint-success').classList.remove('hidden');
    $('#complaint-success').innerHTML=`<div class="success-state"><div class="feature-icon">${icon('check')}</div><h3>Complaint Saved to SOLUM Database!</h3><p>Your ticket reference is <b>${created.id}</b>.<br>Recorded with coordinates (${locationData.lat.toFixed(4)}, ${locationData.lon.toFixed(4)}).</p><div class="subtle">Stored securely in SQLite database and synchronized on the Resolve board.</div><button class="btn" data-close style="margin-top:20px">View ticket</button></div>`;
    $('#complaint-form').reset();
    evidenceURLs.forEach(URL.revokeObjectURL);
    evidenceURLs=[];
    $('#media-preview').replaceChildren();
    if(page==='resolve'){
      $('#issue-filter').value='all';
      renderResolve();
    }
    toast(`Complaint ${created.id} saved to database.`);
  }catch(err){
    const id='SLM-'+Date.now().toString().slice(-7);
    const issue={id,title:subject,place,type:category,icon:icons[category]||'tool',priority:'Unassessed',status:'Assessment',progress:0,crew:0,cost:0,hours:0,owner:'Awaiting assignment',reason:'Logged via complaint dialog.',dependency:'Field verification required',update:description,steps:['Complaint saved','Verification pending'],risk:'Do not enter hazardous areas.',local:true,evidence:[]};
    issues.unshift(issue);
    store.set('issues',issues);
    toast('Saved locally (server was unreachable).');
  }
};

function initReport(){
  $('#land-form').onsubmit=async e=>{
    e.preventDefault();
    const address=$('#land-address').value.trim();
    const use=$('#land-use').value;
    const area=Number($('#land-area').value);
    const lat=Number($('#land-lat').value);
    const lon=Number($('#land-lon').value);
    if(!address)return;

    $('#report-result').classList.remove('hidden');
    $('#report-result').innerHTML=`<article class="card"><p>${icon('layers')} Computing elevation, terrain slope & water proximity via SOLUM Geospatial API…</p></article>`;
    $('#report-result').scrollIntoView({behavior:'smooth',block:'start'});

    try{
      const res=await fetch('/api/land/assess',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({
          address:address,
          proposed_use:use,
          plot_area_sqm:area,
          latitude:lat,
          longitude:lon
        })
      });
      if(!res.ok)throw new Error('Assessment failed');
      const d=await res.json();
      store.set('last_assessment', d);
      window.lastAssessment = d;

      $('#report-result').innerHTML=`<article class="card"><div class="section-head"><div><span class="eyebrow">PRELIMINARY DUE-DILIGENCE REPORT</span><h2 style="font-size:28px">${esc(d.address)}</h2><p style="font-size:12px;margin-top:10px">${esc(d.proposed_use)} · ${d.plot_area_sqm.toLocaleString()} m² · ${d.latitude.toFixed(5)}, ${d.longitude.toFixed(5)}<br>Elevation: <b>${d.elevation_m}m AMSL</b> · Slope: <b>${d.slope_percent}%</b> · Nearest Waterbody: <b>${d.distance_to_water_m}m</b><br>Created ${esc(d.created_at)} · Reference: <b>${esc(d.report_id)}</b></p></div><button class="btn-soft no-print" id="print-report">${icon('download')} Print / Save PDF</button></div><div class="subtle" style="margin-bottom:20px"><b>Readiness: ${esc(d.overall_readiness)}.</b> ${esc(d.summary_note)}</div><div class="table-scroll"><table class="report-matrix"><thead><tr><th>Assessment layer</th><th>Evidence status</th><th>Findings & Recommended Action</th></tr></thead><tbody>${d.matrix.map(r=>`<tr><td>${esc(r.layer)}</td><td>${badge(r.status,r.badge_type)}</td><td>${esc(r.findings)}<br><small style="color:#0f7a37"><b>Recommended:</b> ${esc(r.recommended_action)}</small><p>${r.source_url?`<a class="text-link" href="${esc(r.source_url)}" target="_blank" rel="noopener">${esc(r.reference_source)} ↗</a>`:esc(r.reference_source)}</p></td></tr>`).join('')}</tbody></table></div><h3 style="margin-top:25px">Planning considerations for ${esc(d.proposed_use.toLowerCase())}</h3><p style="font-size:13px">${esc(d.planning_considerations)}</p><h3 style="font-size:16px">Before you commit</h3><p style="font-size:13px">Collect authoritative records → commission site investigations → review with qualified professionals → obtain required approvals. Keep the documents, dates and source references with each finding.</p><p class="source-line">Geospatial analysis computed via Shapely & SOLUM Land Intelligence API. Local statutory requirements apply.</p></article>`;
      $('#print-report').onclick=()=>window.print();
    }catch(err){
      toast('Using standard due diligence template.');
      $('#report-result').innerHTML=`<article class="card"><div class="section-head"><div><span class="eyebrow">PRELIMINARY DUE-DILIGENCE REPORT</span><h2 style="font-size:28px">${esc(address)}</h2><p style="font-size:12px;margin-top:10px">${esc(use)} · ${area.toLocaleString()} m² · ${lat.toFixed(5)}, ${lon.toFixed(5)}</p></div><button class="btn-soft no-print" id="print-report">${icon('download')} Print / Save PDF</button></div><p>Standard due-diligence report generated.</p></article>`;
      $('#print-report').onclick=()=>window.print();
    }
  };
}

async function renderOfficial(){
  const targetDistrict = locationData.district || locationData.name || 'Chennai';
  const targetLocality = locationData.locality || '';

  // 1. Fetch Official Dashboard Stats
  try{
    const statsUrl = `/api/officials/stats?district=${encodeURIComponent(targetDistrict)}${targetLocality ? '&locality=' + encodeURIComponent(targetLocality) : ''}`;
    const stats = await api(statsUrl);
    const grid = $('#official-stats-grid');
    if(grid && stats){
      grid.innerHTML = `
        <div class="official-stat-card"><span>Reported Issues</span><b>${stats.total_reported ?? stats.total_issues ?? 0}</b><small>${esc(targetDistrict)} Jurisdiction</small></div>
        <div class="official-stat-card"><span>In Progress</span><b>${stats.in_progress ?? 0}</b><small>Active field crews</small></div>
        <div class="official-stat-card"><span>Resolved</span><b>${stats.resolved ?? 0}</b><small>Verified restored</small></div>
        <div class="official-stat-card"><span>Pending Next Step</span><b>${stats.pending_issues ?? stats.pending ?? 0}</b><small>Awaiting clearance</small></div>
        <div class="official-stat-card"><span>Critical Priority</span><b style="color:#dc2626">${stats.critical_priority ?? 0}</b><small>Life safety first</small></div>
        <div class="official-stat-card"><span>Assigned Teams</span><b>${stats.assigned_teams ?? 0}</b><small>Dispatched units</small></div>
        <div class="official-stat-card"><span>Repair Progress</span><b>${stats.repair_progress_avg ?? stats.repair_progress_pct ?? 0}%</b><small>Average completion</small></div>
        <div class="official-stat-card"><span>Total Est. Cost</span><b>${money(stats.total_cost || 0)}</b><small>Crew: ${stats.total_crew ?? 0}</small></div>
      `;
    }
  }catch(e){
    console.warn('Official stats fetch note:', e);
  }

  // 2. Fetch Location-Scoped Prioritized Issues
  let priorities=[];
  try{
    const prioUrl = `/api/officials/priorities?district=${encodeURIComponent(targetDistrict)}${targetLocality ? '&locality=' + encodeURIComponent(targetLocality) : ''}`;
    priorities = await api(prioUrl);
  }catch(e){
    const ranks={Critical:0,High:1,Medium:2,Unassessed:3};
    priorities=issues.filter(i=>i.status!=='Resolved').sort((a,b)=>(ranks[a.priority]??3)-(ranks[b.priority]??3));
  }

  const pList = $('#priority-list');
  if(pList){
    if(!priorities.length){
      pList.innerHTML = `<div class="subtle" style="padding:16px 0;text-align:center">No active repair priorities recorded for <b>${esc(targetDistrict)}</b>. All civic systems operating nominally.</div>`;
    }else{
      pList.innerHTML = priorities.map((i,n)=>`
        <div class="priority-row">
          <span class="rank">${n+1}</span>
          <div>
            <b>${esc(i.title)}</b>
            <p>${esc(i.reason)}</p>
            <small style="color:#0f7a37;font-weight:600">${esc(i.locality || i.district || targetDistrict)} · ${esc(i.place || '')}</small>
            <br><small style="color:#64766b">${esc(i.dependency || 'No pending dependencies')}</small>
          </div>
          <div style="text-align:right">
            ${badge(i.priority, i.priority==='Critical'?'red':i.priority==='High'?'amber':'gray')}
            <p style="margin:4px 0 0;font-size:11px">${i.crew?i.crew+' crew':'Unassigned'}</p>
          </div>
        </div>
      `).join('');
    }
  }

  const select = $('#update-issue');
  if(select){
    select.innerHTML = (priorities.length ? priorities : issues).map(i=>`<option value="${esc(i.id)}">${esc(i.id)} · ${esc(i.title)} (${esc(i.district || targetDistrict)})</option>`).join('');
  }

  updateBudget();
  syncUpdateFields();
  renderAudit();
}

function updateBudget(){
  const open=issues.filter(i=>i.status!=='Resolved'),cost=open.reduce((a,i)=>a+i.cost,0),crew=open.reduce((a,i)=>a+i.crew,0),funds=Math.max(0,Number($('#available-funds').value)||0),available=Math.max(0,Number($('#available-crew').value)||0);
  $('#budget-summary').innerHTML=`<div class="row-flex between small"><span>Illustrative work cost</span><b>${money(cost)}</b></div><div class="budget-meter ${cost>funds?'over':''}"><span style="width:${funds?Math.min(100,cost/funds*100):cost?100:0}%"></span></div><div class="details-grid"><div><small>${funds>=cost?'UNALLOCATED FUNDS':'FUNDING GAP'}</small><b>${money(Math.abs(funds-cost))}</b></div><div><small>CREW NEEDED / AVAILABLE</small><b>${crew} / ${available}</b></div></div><div class="subtle">${crew>available?'Crew shortfall: '+(crew-available)+'. Stagger work or request reinforcement.':'Crew capacity covers the active estimate.'}</div>`;
}

function syncUpdateFields(){
  const i=issues.find(x=>x.id===$('#update-issue').value);
  if(!i)return;
  $('#update-status').value=i.status;
  $('#update-progress').value=i.progress;
  $('#update-note').value=i.update;
  $('#update-crew').value=i.crew;
  $('#update-cost').value=i.cost;
  $('#update-hours').value=i.hours;
  $('#update-owner').value=i.owner;
}

async function renderAudit(){
  let logs=[];
  try{
    logs=await api('/api/officials/audit');
  }catch(e){
    logs=store.get('audit',[]);
  }
  $('#audit-log').innerHTML=logs.length?logs.slice(0,5).map(l=>`<div style="border-top:1px solid #e4ece5;padding:10px 0"><b>${esc(l.issue_id||l.id)} · ${esc(l.status)}</b><br>${esc(l.note)}<br><small>${esc(new Date(l.created_at||l.at).toLocaleString())} · ${esc(l.actor_role||'Official update')}</small></div>`).join(''):'No updates recorded yet in database.';
}

function initOfficial(){
  if(officialSession && officialSession.token){
    $('#official-login')?.classList.add('hidden');
    $('#official-workspace')?.classList.remove('hidden');
    const roleLbl = $('#official-role-label');
    if(roleLbl){
      roleLbl.innerHTML = `${icon('shield')} <b>${esc(officialSession.name)}</b> (${esc(officialSession.role)}) · Jurisdiction: <span class="tag amber">${esc(officialSession.district)}</span>`;
    }
    renderOfficial();
  }

  $('#official-login-form').onsubmit = async e => {
    e.preventDefault();
    const oid = $('#official-id').value.trim();
    const passcode = $('#official-passcode').value.trim();
    const role = $('#official-role').value;
    const district = $('#official-district').value;

    try{
      const auth = await api('/api/officials/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ official_id: oid, passcode, role, district })
      });
      officialSession = auth;
      store.set('official_session', auth);
      $('#official-login').classList.add('hidden');
      $('#official-workspace').classList.remove('hidden');
      const roleLbl = $('#official-role-label');
      if(roleLbl){
        roleLbl.innerHTML = `${icon('shield')} <b>${esc(auth.name)}</b> (${esc(auth.role)}) · Jurisdiction: <span class="tag amber">${esc(auth.district)}</span>`;
      }
      toast(`Authenticated as ${auth.name} (${auth.district} jurisdiction).`);
      renderOfficial();
    }catch(err){
      toast('Authentication failed: Invalid credentials or security passcode.');
    }
  };

  $('#official-logout').onclick = () => {
    officialSession = null;
    store.set('official_session', null);
    $('#official-workspace').classList.add('hidden');
    $('#official-login').classList.remove('hidden');
    toast('Logged out from Officials Workspace.');
  };

  $('#available-funds').oninput = updateBudget;
  $('#available-crew').oninput = updateBudget;
  $('#update-issue').onchange = syncUpdateFields;
  $('#update-status').onchange = () => {
    if($('#update-status').value === 'Resolved') $('#update-progress').value = 100;
    else if(+$('#update-progress').value === 100) $('#update-progress').value = 0;
  };

  $('#publish-form').onsubmit = async e => {
    e.preventDefault();
    const issueId = $('#update-issue').value;
    const status = $('#update-status').value;
    const progress = Number($('#update-progress').value);
    const note = $('#update-note').value.trim();
    const crew = Math.max(0, Number($('#update-crew').value));
    const cost = Math.max(0, Number($('#update-cost').value));
    const hours = Math.max(0, Number($('#update-hours').value));
    const owner = $('#update-owner').value.trim();

    if(!note) return;
    if(status !== 'Resolved' && progress === 100){
      toast('Use Resolved for 100% complete work, or lower the progress.');
      return;
    }

    const headers = { 'Content-Type': 'application/json' };
    if(officialSession && officialSession.token){
      headers['X-Official-Token'] = officialSession.token;
      headers['Authorization'] = `Bearer ${officialSession.token}`;
    }

    try{
      const res = await fetch('/api/officials/updates', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          issue_id: issueId,
          status: status,
          progress: progress,
          crew: crew,
          cost: cost,
          hours: hours,
          owner: owner,
          note: note,
          actor_role: officialSession?.role || $('#official-role').value
        })
      });
      if(!res.ok){
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Authorization failed');
      }
      const updated = await res.json();
      const idx = issues.findIndex(x => x.id === issueId);
      if(idx !== -1) issues[idx] = updated;
      store.set('issues', issues);
      await renderAudit();
      renderOfficial();
      toast(`Update for ${issueId} published to SOLUM database.`);
    }catch(err){
      toast(`Server Authorization: ${err.message || 'Permission denied'}`);
    }
  };

  $('#export-plan').onclick = () => {
    const funds = Number($('#available-funds').value);
    const crew = Number($('#available-crew').value);
    const dist = locationData.district || locationData.name || 'Chennai';
    window.location.href = `/api/officials/plan/export?available_funds=${funds}&available_crew=${crew}&district=${encodeURIComponent(dist)}`;
  };
}

function initSolumAi(){
  const trigger = $('#solum-ai-trigger');
  const panel = $('#solum-ai-panel');
  const closeBtn = $('#solum-ai-close');
  const clearBtn = $('#solum-ai-clear');
  const form = $('#solum-ai-form');

  if(trigger && panel){
    trigger.onclick = () => {
      solumAiOpen = !solumAiOpen;
      panel.classList.toggle('hidden', !solumAiOpen);
      if(solumAiOpen) $('#solum-ai-input')?.focus();
    };
  }
  if(closeBtn && panel){
    closeBtn.onclick = () => {
      panel.classList.add('hidden');
      solumAiOpen = false;
    };
  }
  if(clearBtn){
    clearBtn.onclick = () => {
      chatHistory = [];
      const body = $('#solum-ai-body');
      if(body){
        body.innerHTML = `
          <div class="solum-ai-msg bot">
            Hello! I am <b>SOLUM AI</b>, your grounded geospatial assistant for Tamil Nadu.
            Ask me about land assessments, flood risk in your district, emergency kits, or civic repair updates.
            <div class="solum-ai-actions">
              <button type="button" class="solum-ai-action-btn" data-solum-q="Explain flood risks in Madurai vs Chennai">Madurai vs Chennai</button>
              <button type="button" class="solum-ai-action-btn" data-solum-q="What is the 100m waterbody buffer rule?">100m Water Buffer</button>
              <button type="button" class="solum-ai-action-btn" data-solum-q="How do I raise a complaint for fallen wires?">Report Wire Hazard</button>
            </div>
          </div>
        `;
      }
      toast('SOLUM AI conversation history cleared.');
    };
  }
  if(form){
    form.onsubmit = e => {
      e.preventDefault();
      const val = $('#solum-ai-input')?.value;
      if(val) sendSolumAiMessage(val, false);
    };
  }

  document.addEventListener('click', e => {
    const chip = e.target.closest('[data-solum-q]');
    if(chip){
      const q = chip.dataset.solumQ;
      sendSolumAiMessage(q, false);
    }
  });
}

function download(name,content,type){
  const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');
  a.href=url;a.download=name;a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1500);
}

if(page==='index')initHome();
if(page==='prepare')initPrepare();
if(page==='resolve'){$('#issue-filter').onchange=renderResolve;renderResolve();}
if(page==='report')initReport();
if(page==='officials')initOfficial();
initSolumAi();

window.addEventListener('storage',e=>{
  if(e.key==='solum:issues'){
    issues=store.get('issues',issuesSeed);
    if(page==='resolve')renderResolve();
    if(page==='officials'&&!$('#official-workspace').classList.contains('hidden'))renderOfficial();
  }
});
