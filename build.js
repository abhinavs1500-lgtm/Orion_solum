const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('=== SOLUM Production Build for Netlify ===');

// Determine directories
const rootDir = __dirname;
const solumDir = fs.existsSync(path.join(rootDir, 'SOLUM')) 
  ? path.join(rootDir, 'SOLUM') 
  : rootDir;
const distDir = path.join(rootDir, 'dist');

console.log(`Source directory: ${solumDir}`);
console.log(`Output directory: ${distDir}`);

// 1. JavaScript Syntax Validation
console.log('\n[1/5] Validating JavaScript syntax...');
const appJsPath = path.join(solumDir, 'assets', 'app.js');
const sceneJsPath = path.join(solumDir, 'assets', 'scene.js');

if (fs.existsSync(appJsPath)) {
  execSync(`node --check "${appJsPath}"`, { stdio: 'inherit' });
  console.log(' [OK] assets/app.js passed syntax verification');
}
if (fs.existsSync(sceneJsPath)) {
  execSync(`node --check "${sceneJsPath}"`, { stdio: 'inherit' });
  console.log(' [OK] assets/scene.js passed syntax verification');
}

// 2. Prepare Dist Directory
console.log('\n[2/5] Preparing output directory...');
if (fs.existsSync(distDir)) {
  fs.rmSync(distDir, { recursive: true, force: true });
}
fs.mkdirSync(distDir, { recursive: true });

// Helper to copy recursively
function copyRecursiveSync(src, dest) {
  const exists = fs.existsSync(src);
  const stats = exists && fs.statSync(src);
  const isDirectory = exists && stats.isDirectory();
  if (isDirectory) {
    if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
    fs.readdirSync(src).forEach((childItemName) => {
      copyRecursiveSync(path.join(src, childItemName), path.join(dest, childItemName));
    });
  } else if (exists) {
    const parentDir = path.dirname(dest);
    if (!fs.existsSync(parentDir)) fs.mkdirSync(parentDir, { recursive: true });
    fs.copyFileSync(src, dest);
  }
}

// 3. Copy Web Pages and Assets
console.log('\n[3/5] Bundling HTML pages and static assets...');
const backendUrl = (process.env.BACKEND_URL || process.env.SOLUM_API_BASE || '').trim().replace(/\/+$/, '');
const pages = ['index.html', 'prepare.html', 'resolve.html', 'report.html', 'officials.html'];
pages.forEach((p) => {
  const src = path.join(solumDir, p);
  if (fs.existsSync(src)) {
    let content = fs.readFileSync(src, 'utf8');
    if (backendUrl) {
      content = content.replace('</head>', `<script>window.SOLUM_API_BASE = ${JSON.stringify(backendUrl)};</script>\n</head>`);
    }
    fs.writeFileSync(path.join(distDir, p), content, 'utf8');
    console.log(` [OK] Bundled ${p}${backendUrl ? ' (injected SOLUM_API_BASE)' : ''}`);
  }
});

const assetsSrc = path.join(solumDir, 'assets');
if (fs.existsSync(assetsSrc)) {
  copyRecursiveSync(assetsSrc, path.join(distDir, 'assets'));
  console.log(' [OK] Bundled assets directory (CSS, JS, Fonts, Images)');
}

// 4. Generate Fallback Static Endpoints for Netlify
console.log('\n[4/5] Generating static API endpoints & security configuration...');
const apiDir = path.join(distDir, 'api');
fs.mkdirSync(path.join(apiDir, 'maps'), { recursive: true });
fs.mkdirSync(path.join(apiDir, 'issues'), { recursive: true });
fs.mkdirSync(path.join(apiDir, 'officials'), { recursive: true });

// Read Maps API key from environment variable or bundled default
const googleMapsApiKey = process.env.GOOGLE_MAPS_API_KEY || 'AIzaSyAOWcDHEha2UfkgMVCRou4YKTNLIswN8BE';
const mapsConfig = {
  api_key: googleMapsApiKey,
  default_center: { lat: 13.0827, lng: 80.2707, altitude: 450.0 },
  default_tilt: 60.0,
  default_heading: 20.0,
  default_range: 1200.0
};
fs.writeFileSync(path.join(apiDir, 'maps', 'config.json'), JSON.stringify(mapsConfig, null, 2));

const appConfig = {
  api_base: backendUrl,
  google_maps_api_key: googleMapsApiKey,
  status: "configured"
};
fs.writeFileSync(path.join(apiDir, 'config.json'), JSON.stringify(appConfig, null, 2));

// Seeded news fallback
const newsData = {
  region: 'Tamil Nadu',
  scope: 'district',
  count: 3,
  items: [
    {
      title: "IMD Doppler Radar active across Tamil Nadu basins.",
      summary: "Regional Meteorological Centre issues regular monsoon monitoring bulletins for coastal and delta districts.",
      publisher: "IMD Regional Centre",
      url: "https://mausam.imd.gov.in/chennai/",
      kind: "WEATHER BULLETIN",
      image_url: "assets/images/news/monsoon-radar.svg",
      image_caption: "Illustrative: IMD Doppler radar & monsoon forecast tracking"
    },
    {
      title: "Stormwater drainage maintenance underway.",
      summary: "Pumping units and desilt operations staged across critical catchment arterial routes.",
      publisher: "Municipal Administration",
      url: "https://chennaicorporation.gov.in/",
      kind: "CIVIC INFRASTRUCTURE",
      image_url: "assets/images/news/stormwater-drainage.svg",
      image_caption: "Illustrative: Municipal stormwater & community preparedness"
    },
    {
      title: "Wetland & lake buffer conservation guidelines updated.",
      summary: "Geospatial 100m catchment boundary verification recommended before planning civic structures.",
      publisher: "Tamil Nadu Water Resources",
      url: "https://bhuvan.nrsc.gov.in/",
      kind: "LAND CONSERVATION",
      image_url: "assets/images/news/waterbody-restoration.svg",
      image_caption: "Illustrative: Wetland & waterbody conservation"
    }
  ]
};
fs.writeFileSync(path.join(apiDir, 'news.json'), JSON.stringify(newsData, null, 2));

// Seeded multi-district issues fallback for production Netlify
const issuesData = [
  {id:'SLM-1042',title:'Power line damage',place:'Velachery Main Road',district:'Chennai',locality:'Velachery',latitude:12.9815,longitude:80.2180,type:'Electricity',icon:'bolt',priority:'Critical',status:'In progress',progress:45,crew:8,cost:240000,hours:6,owner:'Electricity response team',reason:'Isolate electrical hazards before pumping or road clearance.',dependency:'Isolation clearance before SLM-1043',update:'Isolation completed; replacement pole and cable crew assigned.',steps:['Citizen report received','Electrical isolation confirmed','Replacement work in progress','Inspection and safe restoration'],risk:'Keep clear of fallen wires and flooded electrical equipment.'},
  {id:'SLM-1043',title:'Waterlogging near homes',place:'Ram Nagar · Velachery',district:'Chennai',locality:'Velachery',latitude:12.9750,longitude:80.2210,type:'Drainage',icon:'water',priority:'High',status:'In progress',progress:30,crew:6,cost:180000,hours:8,owner:'Stormwater drainage team',reason:'Restore access to homes after electrical clearance.',dependency:'Depends on SLM-1042 isolation',update:'Pumps staged; electrical clearance is required before entry.',steps:['Site assessed','Pumping team allocated','Pumping and drain clearance','Access inspected'],risk:'Do not walk or drive through floodwater.'},
  {id:'SLM-1044',title:'Fallen tree blocking access',place:'Taramani Link Road',district:'Chennai',locality:'Taramani',latitude:12.9860,longitude:80.2420,type:'Roads',icon:'tree',priority:'High',status:'Assigned',progress:15,crew:5,cost:65000,hours:4,owner:'Road clearance team',reason:'Open an access corridor for response vehicles.',dependency:'Confirm nearby wires are isolated',update:'Tree-removal crew assigned; access inspection pending.',steps:['Obstruction reported','Crew assigned','Tree removal','Road reopened after inspection'],risk:'Keep away from unstable trees and overhead wires.'},
  {id:'SLM-1045',title:'Damaged mobile network tower',place:'Pallikaranai · service area',district:'Chennai',locality:'Pallikaranai',latitude:12.9350,longitude:80.2138,type:'Telecom',icon:'network',priority:'Medium',status:'Assessment',progress:5,crew:4,cost:320000,hours:18,owner:'Telecom restoration team',reason:'Restore communication after structure and access checks.',dependency:'Structural inspection required',update:'Structural review requested; temporary coverage plan pending.',steps:['Service loss logged','Structural assessment','Repair or temporary service','Coverage verified'],risk:'Stay outside the cordoned area.'},
  {id:'SLM-1046',title:'Blocked roadside drain',place:'Vijaya Nagar · junction',district:'Chennai',locality:'Velachery',latitude:12.9790,longitude:80.2240,type:'Drainage',icon:'water',priority:'Medium',status:'Resolved',progress:100,crew:3,cost:45000,hours:3,owner:'Drainage maintenance team',reason:'Remove a local blockage and confirm drainage flow.',dependency:'No open dependencies',update:'Drain cleared and flow checked in this demonstration record.',steps:['Blockage logged','Crew assigned','Debris removed','Flow checked and closure recorded'],risk:'Avoid open drains; follow barriers at the work site.'},
  {id:'SLM-2011',title:'Stormwater culvert siltation',place:'Anna Nagar 2nd Avenue',district:'Chennai',locality:'Anna Nagar',latitude:13.0850,longitude:80.2100,type:'Drainage',icon:'water',priority:'High',status:'In progress',progress:35,crew:6,cost:120000,hours:5,owner:'Corporation Stormwater Team',reason:'Clear trunk line before monsoon rains.',dependency:'No open dependencies',update:'Suction vehicle deployed; silt traps cleaned.',steps:['Report logged','Culvert inspection','Desilting underway','Flow verified'],risk:'Follow traffic diversion signs around work zones.'},
  {id:'SLM-2021',title:'Lake bund overflow alert',place:'Singanallur Lake Bund Road',district:'Coimbatore',locality:'Singanallur',latitude:11.0016,longitude:77.0264,type:'Drainage',icon:'water',priority:'High',status:'In progress',progress:50,crew:8,cost:220000,hours:6,owner:'Coimbatore City Municipal Corp',reason:'Regulate surplus sluice to prevent roadway inundation.',dependency:'Sluice gate check completed',update:'Sandbag revetment reinforced along low-lying bund section.',steps:['Inundation alert logged','Sluice inspection','Bund revetment work','Water level stabilization'],risk:'Do not walk on lake embankments during high water.'},
  {id:'SLM-2022',title:'Distribution pipeline rupture',place:'DB Road · RS Puram',district:'Coimbatore',locality:'RS Puram',latitude:11.0125,longitude:76.9480,type:'Drainage',icon:'water',priority:'Medium',status:'Assigned',progress:20,crew:5,cost:85000,hours:4,owner:'TWAD & City Water Division',reason:'Isolate burst line and bypass supply to residential blocks.',dependency:'Pumping isolation required',update:'Excavation permit approved; pipe replacement crew staged.',steps:['Leak reported','Valve isolated','Excavation and pipe join','Pressure test and road patch'],risk:'Avoid open excavation on DB Road.'},
  {id:'SLM-2031',title:'Streetlight feeder pillar fault',place:'Goripalayam Riverfront Road',district:'Madurai',locality:'Goripalayam',latitude:9.9320,longitude:78.1310,type:'Electricity',icon:'bolt',priority:'High',status:'In progress',progress:60,crew:4,cost:95000,hours:3,owner:'TANGEDCO Urban Sub-division',reason:'Isolate short circuit near Vaigai riverbank footpath.',dependency:'Isolation confirmed',update:'Underground cable spliced; safety earthing re-tested.',steps:['Citizen report received','Pillar isolated','Cable splicing','Energisation check'],risk:'Do not touch damp streetlight pillars.'},
  {id:'SLM-2032',title:'Bus terminal stormwater drain choke',place:'Mattuthavani Central Bus Stand',district:'Madurai',locality:'Mattuthavani',latitude:9.9485,longitude:78.1560,type:'Drainage',icon:'water',priority:'Medium',status:'Assessment',progress:10,crew:4,cost:60000,hours:4,owner:'Madurai Corporation Sanitation',reason:'Prevent terminal bay water accumulation during evening downpour.',dependency:'Awaiting vacuum desilter',update:'Field assessment completed; desilting scheduled tonight.',steps:['Grievance logged','Terminal bay inspected','Mechanical clearing scheduled','Inspection'],risk:'Caution: Slippery apron around bus bays.'},
  {id:'SLM-2041',title:'Culvert erosion after rainfall',place:'Hasthampatti Main Road',district:'Salem',locality:'Hasthampatti',latitude:11.6750,longitude:78.1560,type:'Roads',icon:'tree',priority:'High',status:'In progress',progress:40,crew:6,cost:175000,hours:8,owner:'Salem Highways & Works',reason:'Restore shoulder support and culvert wing-wall.',dependency:'Traffic diversion implemented',update:'Gabion masonry retaining wall being placed.',steps:['Shoulder scour logged','Barricades erected','Retaining wall masonry','Resurfacing'],risk:'Heavy vehicles redirected via alternate bypass.'},
  {id:'SLM-2051',title:'Temple road stormwater line desilting',place:'Srirangam North Chithirai St',district:'Tiruchirappalli',locality:'Srirangam',latitude:10.8624,longitude:78.6946,type:'Drainage',icon:'water',priority:'Medium',status:'Resolved',progress:100,crew:4,cost:52000,hours:4,owner:'Trichy Corporation Drainage Wing',reason:'Clear silt from underground chamber before festival procession.',dependency:'No open dependencies',update:'Complete desilting and chamber cover replacement finalized.',steps:['Blockage reported','Team dispatched','Chamber cleared','Flow certified'],risk:'Work completed; pedestrian flow restored.'},
  {id:'SLM-2061',title:'Landslip mud clearance on ghat road',place:'Coonoor-Ooty Ghat KM 14',district:'Nilgiris',locality:'Ooty',latitude:11.4102,longitude:76.6950,type:'Roads',icon:'tree',priority:'Critical',status:'In progress',progress:70,crew:12,cost:340000,hours:5,owner:'State Highways Ghat Division',reason:'Clear road obstruction and stabilize uphill soil slope.',dependency:'Controlled single-lane traffic',update:'Excavator clearing debris; rock netting being installed.',steps:['Slope failure reported','Traffic halted','Debris clearing','Slope netting and reopening'],risk:'Extreme caution: Wet slippery slope; avoid night travel.'},
  {id:'SLM-2071',title:'Coastal seawall boulder shift check',place:'Beach Promenade Road',district:'Kanniyakumari',locality:'Kanyakumari',latitude:8.0883,longitude:77.5385,type:'Roads',icon:'tree',priority:'Medium',status:'Assessment',progress:15,crew:4,cost:110000,hours:6,owner:'PWD Coastal Engineering',reason:'Check tetrapod and boulder armor displacement after high tide.',dependency:'Hydrographic report pending',update:'Initial visual survey completed; crane mobilization planned.',steps:['Displacement observed','Visual survey logged','Armor repositioning','Final inspection'],risk:'Stay off wet tetrapods and outer seawall slope.'}
];
fs.writeFileSync(path.join(apiDir, 'issues.json'), JSON.stringify(issuesData, null, 2));

const issuesStats = {
  total: 5,
  open: 4,
  in_progress: 2,
  resolved: 1,
  by_category: { Electricity: 1, Drainage: 2, Roads: 1, Telecom: 1 },
  by_priority: { Critical: 1, High: 2, Medium: 2 }
};
fs.writeFileSync(path.join(apiDir, 'issues', 'stats.json'), JSON.stringify(issuesStats, null, 2));

const prioData = [
  { rank: 1, id: 'SLM-1042', title: 'Power line damage', priority: 'Critical', district: 'Chennai', status: 'In progress' },
  { rank: 2, id: 'SLM-1043', title: 'Waterlogging near homes', priority: 'High', district: 'Chennai', status: 'In progress' }
];
fs.writeFileSync(path.join(apiDir, 'officials', 'priorities.json'), JSON.stringify(prioData, null, 2));

const officialStats = {
  total_issues: 5,
  pending_issues: 1,
  in_progress_issues: 2,
  resolved_issues: 1,
  critical_issues: 1,
  overall_progress_pct: 38.0,
  active_crews: 26,
  total_budget_spent: 850000,
  jurisdiction: 'Chennai'
};
fs.writeFileSync(path.join(apiDir, 'officials', 'stats.json'), JSON.stringify(officialStats, null, 2));

// 5. Generate Netlify Routing Files
console.log('\n[5/5] Generating Netlify _redirects and _headers...');
const redirectsContent = `# Netlify Clean URL & Single-Page Redirects
/prepare       /prepare.html       200
/resolve       /resolve.html       200
/report        /report.html        200
/officials     /officials.html     200

# API mock rewrites
/api/maps/config          /api/maps/config.json          200
/api/news                 /api/news.json                 200
/api/issues/stats         /api/issues/stats.json         200
/api/issues               /api/issues.json               200
/api/officials/priorities /api/officials/priorities.json 200
/api/officials/stats      /api/officials/stats.json      200
`;
fs.writeFileSync(path.join(distDir, '_redirects'), redirectsContent);

const headersContent = `/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin

/assets/*
  Cache-Control: public, max-age=31536000, immutable
`;
fs.writeFileSync(path.join(distDir, '_headers'), headersContent);

console.log('\n=== SOLUM Build Succeeded! Output ready in dist/ ===');
