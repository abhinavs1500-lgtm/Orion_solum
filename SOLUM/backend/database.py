import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator
from backend.config import settings

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db_session() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS issues (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            place TEXT NOT NULL,
            district TEXT NOT NULL DEFAULT 'Chennai',
            city TEXT NOT NULL DEFAULT 'Chennai',
            locality TEXT NOT NULL DEFAULT 'Velachery',
            latitude REAL,
            longitude REAL,
            type TEXT NOT NULL,
            icon TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            crew INTEGER NOT NULL DEFAULT 0,
            cost INTEGER NOT NULL DEFAULT 0,
            hours INTEGER NOT NULL DEFAULT 0,
            owner TEXT NOT NULL,
            reason TEXT NOT NULL,
            dependency TEXT NOT NULL,
            latest_update TEXT NOT NULL,
            steps_json TEXT NOT NULL,
            risk_advisory TEXT NOT NULL,
            evidence_json TEXT,
            data_source TEXT NOT NULL DEFAULT 'Demonstration baseline (SOLUM)',
            record_type TEXT NOT NULL DEFAULT 'demonstration',
            is_local_submission BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT NOT NULL,
            actor_role TEXT,
            crew_allocated INTEGER,
            cost_allocated INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY(issue_id) REFERENCES issues(id)
        );

        CREATE TABLE IF NOT EXISTS land_reports (
            id TEXT PRIMARY KEY,
            site_address TEXT NOT NULL,
            proposed_use TEXT NOT NULL,
            plot_area_sqm REAL NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            elevation_m REAL,
            slope_percent REAL,
            water_distance_m REAL,
            flood_risk_level TEXT NOT NULL,
            matrix_json TEXT NOT NULL,
            recommendations_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS evidence_files (
            id TEXT PRIMARY KEY,
            issue_id TEXT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY(issue_id) REFERENCES issues(id)
        );
        """)

        # Migration: Ensure new columns exist on older tables
        cols = [r[1] for r in conn.execute("PRAGMA table_info(issues)").fetchall()]
        for col_name, col_type, col_def in [
            ("district", "TEXT", "'Chennai'"),
            ("city", "TEXT", "'Chennai'"),
            ("locality", "TEXT", "'Velachery'"),
            ("data_source", "TEXT", "'Demonstration baseline (SOLUM)'"),
            ("record_type", "TEXT", "'demonstration'")
        ]:
            if col_name not in cols:
                conn.execute(f"ALTER TABLE issues ADD COLUMN {col_name} {col_type} DEFAULT {col_def}")

        # Deduplicate duplicate test submissions
        conn.execute("""
            DELETE FROM issues WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM issues GROUP BY title, place
            ) AND title LIKE 'Fallen transmission wire%'
        """)

        # Backfill location fields on existing records
        conn.execute("UPDATE issues SET district='Chennai', city='Chennai', locality='Velachery' WHERE id IN ('SLM-1042','SLM-1043','SLM-1046')")
        conn.execute("UPDATE issues SET district='Chennai', city='Chennai', locality='Taramani' WHERE id='SLM-1044'")
        conn.execute("UPDATE issues SET district='Chennai', city='Chennai', locality='Pallikaranai' WHERE id='SLM-1045'")
        conn.execute("UPDATE issues SET district='Chennai', city='Chennai', locality='Velachery' WHERE title LIKE 'Fallen transmission wire%'")

        # Seed demonstration records for Tamil Nadu target locations (idempotent INSERT OR IGNORE)
        now = datetime.now(timezone.utc).isoformat()
        tn_seeds = [
            (
                "SLM-1042", "Power line damage", "Velachery Main Road", "Chennai", "Chennai", "Velachery",
                12.9815, 80.2180, "Electricity", "bolt", "Critical", "In progress",
                45, 8, 240000, 6, "Electricity response team",
                "Isolate electrical hazards before pumping or road clearance.", "Isolation clearance before SLM-1043",
                "Isolation completed; replacement pole and cable crew assigned.",
                json.dumps(["Citizen report received", "Electrical isolation confirmed", "Replacement work in progress", "Inspection and safe restoration"]),
                "Keep clear of fallen wires and flooded electrical equipment.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-1043", "Waterlogging near homes", "Ram Nagar · Velachery", "Chennai", "Chennai", "Velachery",
                12.9750, 80.2210, "Drainage", "water", "High", "In progress",
                30, 6, 180000, 8, "Stormwater drainage team",
                "Restore access to homes after electrical clearance.", "Depends on SLM-1042 isolation",
                "Pumps staged; electrical clearance is required before entry.",
                json.dumps(["Site assessed", "Pumping team allocated", "Pumping and drain clearance", "Access inspected"]),
                "Do not walk or drive through floodwater.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-1044", "Fallen tree blocking access", "Taramani Link Road", "Chennai", "Chennai", "Taramani",
                12.9860, 80.2420, "Roads", "tree", "High", "Assigned",
                15, 5, 65000, 4, "Road clearance team",
                "Open an access corridor for response vehicles.", "Confirm nearby wires are isolated",
                "Tree-removal crew assigned; access inspection pending.",
                json.dumps(["Obstruction reported", "Crew assigned", "Tree removal", "Road reopened after inspection"]),
                "Keep away from unstable trees and overhead wires.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-1045", "Damaged mobile network tower", "Pallikaranai · service area", "Chennai", "Chennai", "Pallikaranai",
                12.9350, 80.2138, "Telecom", "network", "Medium", "Assessment",
                5, 4, 320000, 18, "Telecom restoration team",
                "Restore communication after structure and access checks.", "Structural inspection required",
                "Structural review requested; temporary coverage plan pending.",
                json.dumps(["Service loss logged", "Structural assessment", "Repair or temporary service", "Coverage verified"]),
                "Stay outside the cordoned area.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-1046", "Blocked roadside drain", "Vijaya Nagar · junction", "Chennai", "Chennai", "Velachery",
                12.9790, 80.2240, "Drainage", "water", "Medium", "Resolved",
                100, 3, 45000, 3, "Drainage maintenance team",
                "Remove a local blockage and confirm drainage flow.", "No open dependencies",
                "Drain cleared and flow checked in this demonstration record.",
                json.dumps(["Blockage logged", "Crew assigned", "Debris removed", "Flow checked and closure recorded"]),
                "Avoid open drains; follow barriers at the work site.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-2011", "Stormwater culvert siltation", "Anna Nagar 2nd Avenue", "Chennai", "Chennai", "Anna Nagar",
                13.0850, 80.2100, "Drainage", "water", "High", "In progress",
                35, 6, 120000, 5, "Corporation Stormwater Team",
                "Clear trunk line before monsoon rains.", "No open dependencies",
                "Suction vehicle deployed; silt traps cleaned.",
                json.dumps(["Report logged", "Culvert inspection", "Desilting underway", "Flow verified"]),
                "Follow traffic diversion signs around work zones.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-2021", "Lake bund overflow alert", "Singanallur Lake Bund Road", "Coimbatore", "Coimbatore", "Singanallur",
                11.0016, 77.0264, "Drainage", "water", "High", "In progress",
                50, 8, 220000, 6, "Coimbatore City Municipal Corp",
                "Regulate surplus sluice to prevent roadway inundation.", "Sluice gate check completed",
                "Sandbag revetment reinforced along low-lying bund section.",
                json.dumps(["Inundation alert logged", "Sluice inspection", "Bund revetment work", "Water level stabilization"]),
                "Do not walk on lake embankments during high water.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-2022", "Distribution pipeline rupture", "DB Road · RS Puram", "Coimbatore", "Coimbatore", "RS Puram",
                11.0125, 76.9480, "Drainage", "water", "Medium", "Assigned",
                20, 5, 85000, 4, "TWAD & City Water Division",
                "Isolate burst line and bypass supply to residential blocks.", "Pumping isolation required",
                "Excavation permit approved; pipe replacement crew staged.",
                json.dumps(["Leak reported", "Valve isolated", "Excavation and pipe join", "Pressure test and road patch"]),
                "Avoid open excavation on DB Road.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-2031", "Streetlight feeder pillar fault", "Goripalayam Riverfront Road", "Madurai", "Madurai", "Goripalayam",
                9.9320, 78.1310, "Electricity", "bolt", "High", "In progress",
                60, 4, 95000, 3, "TANGEDCO Urban Sub-division",
                "Isolate short circuit near Vaigai riverbank footpath.", "Isolation confirmed",
                "Underground cable spliced; safety earthing re-tested.",
                json.dumps(["Citizen report received", "Pillar isolated", "Cable splicing", "Energisation check"]),
                "Do not touch damp streetlight pillars.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-2032", "Bus terminal stormwater drain choke", "Mattuthavani Central Bus Stand", "Madurai", "Madurai", "Mattuthavani",
                9.9485, 78.1560, "Drainage", "water", "Medium", "Assessment",
                10, 4, 60000, 4, "Madurai Corporation Sanitation",
                "Prevent terminal bay water accumulation during evening downpour.", "Awaiting vacuum desilter",
                "Field assessment completed; desilting scheduled tonight.",
                json.dumps(["Grievance logged", "Terminal bay inspected", "Mechanical clearing scheduled", "Inspection"]),
                "Caution: Slippery apron around bus bays.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-2041", "Culvert erosion after rainfall", "Hasthampatti Main Road", "Salem", "Salem", "Hasthampatti",
                11.6750, 78.1560, "Roads", "tree", "High", "In progress",
                40, 6, 175000, 8, "Salem Highways & Works",
                "Restore shoulder support and culvert wing-wall.", "Traffic diversion implemented",
                "Gabion masonry retaining wall being placed.",
                json.dumps(["Shoulder scour logged", "Barricades erected", "Retaining wall masonry", "Resurfacing"]),
                "Heavy vehicles redirected via alternate bypass.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-2051", "Temple road stormwater line desilting", "Srirangam North Chithirai St", "Tiruchirappalli", "Tiruchirappalli", "Srirangam",
                10.8624, 78.6946, "Drainage", "water", "Medium", "Resolved",
                100, 4, 52000, 4, "Trichy Corporation Drainage Wing",
                "Clear silt from underground chamber before festival procession.", "No open dependencies",
                "Complete desilting and chamber cover replacement finalized.",
                json.dumps(["Blockage reported", "Team dispatched", "Chamber cleared", "Flow certified"]),
                "Work completed; pedestrian flow restored.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-2061", "Landslip mud clearance on ghat road", "Coonoor-Ooty Ghat KM 14", "Nilgiris", "Udhagamandalam", "Ooty",
                11.4102, 76.6950, "Roads", "tree", "Critical", "In progress",
                70, 12, 340000, 5, "State Highways Ghat Division",
                "Clear road obstruction and stabilize uphill soil slope.", "Controlled single-lane traffic",
                "Excavator clearing debris; rock netting being installed.",
                json.dumps(["Slope failure reported", "Traffic halted", "Debris clearing", "Slope netting and reopening"]),
                "Extreme caution: Wet slippery slope; avoid night travel.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            ),
            (
                "SLM-2071", "Coastal seawall boulder shift check", "Beach Promenade Road", "Kanyakumari", "Kanyakumari", "Kanyakumari",
                8.0883, 77.5385, "Roads", "tree", "Medium", "Assessment",
                15, 4, 110000, 6, "PWD Coastal Engineering",
                "Check tetrapod and boulder armor displacement after high tide.", "Hydrographic report pending",
                "Initial visual survey completed; crane mobilization planned.",
                json.dumps(["Displacement observed", "Visual survey logged", "Armor repositioning", "Final inspection"]),
                "Stay off wet tetrapods and outer seawall slope.", json.dumps([]),
                "Demonstration baseline (SOLUM)", "demonstration", 0, now, now
            )
        ]

        conn.executemany("""
        INSERT OR IGNORE INTO issues (
            id, title, place, district, city, locality, latitude, longitude, type, icon, priority, status,
            progress, crew, cost, hours, owner, reason, dependency, latest_update,
            steps_json, risk_advisory, evidence_json, data_source, record_type, is_local_submission,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tn_seeds)
