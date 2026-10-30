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
const pages = ['index.html', 'prepare.html', 'resolve.html', 'report.html', 'officials.html'];
pages.forEach((p) => {
  const src = path.join(solumDir, p);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, path.join(distDir, p));
    console.log(` [OK] Bundled ${p}`);
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

// Read Maps API key securely from environment variable
const googleMapsApiKey = process.env.GOOGLE_MAPS_API_KEY || '';
const mapsConfig = {
  api_key: googleMapsApiKey,
  default_center: { lat: 13.0827, lng: 80.2707, altitude: 450.0 },
  default_tilt: 60.0,
  default_heading: 20.0,
  default_range: 1200.0
};
fs.writeFileSync(path.join(apiDir, 'maps', 'config.json'), JSON.stringify(mapsConfig, null, 2));

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

// Seeded issues fallback
const issuesData = [
  {
    id: 'SLM-1042',
    title: 'Power line damage',
    place: 'Velachery Main Road',
    type: 'Electricity',
    district: 'Chennai',
    priority: 'Critical',
    status: 'In progress',
    progress: 45,
    crew: 8,
    cost: 240000,
    hours: 6,
    owner: 'Electricity response team',
    reason: 'Isolate electrical hazards before pumping or road clearance.',
    dependency: 'Isolation clearance before SLM-1043',
    update: 'Isolation completed; replacement pole and cable crew assigned.',
    steps: ['Citizen report received', 'Electrical isolation confirmed', 'Replacement work in progress', 'Inspection and safe restoration'],
    risk: 'Keep clear of fallen wires and flooded electrical equipment.'
  },
  {
    id: 'SLM-1043',
    title: 'Waterlogging near homes',
    place: 'Ram Nagar · Velachery',
    type: 'Drainage',
    district: 'Chennai',
    priority: 'High',
    status: 'In progress',
    progress: 30,
    crew: 6,
    cost: 180000,
    hours: 8,
    owner: 'Stormwater drainage team',
    reason: 'Restore access to homes after electrical clearance.',
    dependency: 'Depends on SLM-1042 isolation',
    update: 'Pumps staged; electrical clearance is required before entry.',
    steps: ['Site assessed', 'Pumping team allocated', 'Pumping and drain clearance', 'Access inspected'],
    risk: 'Do not walk or drive through floodwater.'
  },
  {
    id: 'SLM-1044',
    title: 'Fallen tree blocking access',
    place: 'Taramani Link Road',
    type: 'Roads',
    district: 'Chennai',
    priority: 'High',
    status: 'Assigned',
    progress: 15,
    crew: 5,
    cost: 65000,
    hours: 4,
    owner: 'Road clearance team',
    reason: 'Open an access corridor for response vehicles.',
    dependency: 'Confirm nearby wires are isolated',
    update: 'Tree-removal crew assigned; access inspection pending.',
    steps: ['Obstruction reported', 'Crew assigned', 'Tree removal', 'Road reopened after inspection'],
    risk: 'Keep away from unstable trees and overhead wires.'
  }
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
