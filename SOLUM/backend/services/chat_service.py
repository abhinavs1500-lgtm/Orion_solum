import os
import re
import json
import httpx
from typing import List, Dict, Any, Optional
from backend.models import ChatRequest, ChatResponse, ChatAction
from backend.services.issues_service import list_issues

# Tamil Nadu District Geospatial Profiles for SOLUM AI
TN_DISTRICT_PROFILES = {
    "chennai": {
        "elevation": "6–15m AMSL (Lowland coastal plain)",
        "water_corridors": "Adyar, Cooum rivers, Buckingham Canal, Pallikaranai Marshland",
        "primary_risks": "Monsoonal urban waterlogging, tidal backwater surges, convective cloudbursts",
        "planning_notes": "100m statutory buffer around waterbodies is strictly enforced by CMDA. Low terrain slope requires gravity flap valves and stormwater pumps."
    },
    "coimbatore": {
        "elevation": "410–430m AMSL (Inland elevated plateau, foothills of Western Ghats)",
        "water_corridors": "Noyyal River basin, Singanallur Lake, Valankulam, Ukkadam Lake cascade",
        "primary_risks": "Seasonal lake bund overflow, Noyyal flash runoff, groundwater depletion in non-monsoon months",
        "planning_notes": "Significant elevation gradient; verify cut-and-fill slope stability and downstream retention before construction."
    },
    "madurai": {
        "elevation": "130–145m AMSL (Semi-arid inland river basin)",
        "water_corridors": "Vaigai River corridor, Vandiyur Lake, seasonal irrigation tank cascades",
        "primary_risks": "Flash runoff during northeast monsoon downpours, riverfront embankment scour, prolonged summer heat",
        "planning_notes": "Vaigai riverfront setbacks require special PWD clearances; check tank catchment bund integrity."
    },
    "salem": {
        "elevation": "275–300m AMSL (Inter-montane valley bounded by Shevaroy Hills)",
        "water_corridors": "Thirumanimutharu River, Mookaneri Lake",
        "primary_risks": "Runoff velocity from steep surrounding hillsides, culvert erosion, localized urban flash inundation",
        "planning_notes": "Foot-slope drainage corridors must be preserved to prevent hill torrent damage to roads."
    },
    "tiruchirappalli": {
        "elevation": "75–88m AMSL (Cauvery-Coleroon delta apex)",
        "water_corridors": "Cauvery River, Coleroon River, Uyyakondan canal system",
        "primary_risks": "Cauvery surplus release flooding, canal siltation, high seasonal water table",
        "planning_notes": "Deltaic silt and sand strata require careful structural bearing capacity verification."
    },
    "nilgiris": {
        "elevation": "1,800–2,600m AMSL (Steep Western Ghats montane ridge)",
        "water_corridors": "Pykara, Moyar rivers, steep seasonal stream ravines",
        "primary_risks": "High-slope landslides, debris flows on road cuts, lateritic soil shear failure during continuous rains",
        "planning_notes": "Hill Area Conservation Authority (HACA) approval mandatory; retaining walls and hillside subsoil drainage strictly required."
    },
    "kanyakumari": {
        "elevation": "0–40m AMSL (Coastal peninsular junction)",
        "water_corridors": "Pazhayar River, Indian Ocean / Arabian Sea / Bay of Bengal shoreline",
        "primary_risks": "High wave action, coastal erosion, severe pre-monsoon convective squalls",
        "planning_notes": "Coastal Regulation Zone (CRZ) rules apply within 500m of high tide line."
    }
}

def extract_subject_district(message: str, history: List[Any], context_loc: Optional[str]) -> str:
    """Infers the geographical district being discussed across multi-turn turns."""
    msg = message.lower()
    for d in TN_DISTRICT_PROFILES.keys():
        if d in msg:
            return d
            
    # Check history backwards for the most recent mentioned district
    if history:
        for turn in reversed(history):
            content = turn.content.lower() if hasattr(turn, 'content') else str(turn.get('content', '')).lower()
            for d in TN_DISTRICT_PROFILES.keys():
                if d in content:
                    return d
                    
    # Fallback to selected location context
    if context_loc:
        cl = context_loc.lower()
        for d in TN_DISTRICT_PROFILES.keys():
            if d in cl:
                return d
    return "chennai"

def generate_reasoning_reply(
    message: str,
    history: List[Any],
    context: Optional[Dict[str, Any]],
    location_name: str,
    district_key: str
) -> ChatResponse:
    q = message.lower().strip()
    profile = TN_DISTRICT_PROFILES.get(district_key, TN_DISTRICT_PROFILES["chennai"])
    dist_display = district_key.capitalize() if district_key != "nilgiris" else "The Nilgiris"

    actions: List[ChatAction] = []
    suggested: List[str] = []

    # 1. Comparison Queries (e.g. "compare it with Chennai", "compare Coimbatore with Madurai")
    if "compare" in q:
        comp_dist = "chennai" if district_key != "chennai" else "coimbatore"
        for d in TN_DISTRICT_PROFILES.keys():
            if d in q and d != district_key:
                comp_dist = d
                break
        comp_prof = TN_DISTRICT_PROFILES[comp_dist]
        comp_display = comp_dist.capitalize() if comp_dist != "nilgiris" else "The Nilgiris"
        
        reply = (
            f"Here is a geographical comparison between **{dist_display}** and **{comp_display}**:\n\n"
            f"• **Terrain & Elevation**: {dist_display} sits at {profile['elevation']}, whereas {comp_display} is at {comp_prof['elevation']}.\n\n"
            f"• **Water Systems**: {dist_display} is shaped by the {profile['water_corridors']}, while {comp_display} is influenced by {comp_prof['water_corridors']}.\n\n"
            f"• **Key Hazards**: {dist_display} primarily contends with {profile['primary_risks']}. In contrast, {comp_display} faces {comp_prof['primary_risks']}.\n\n"
            f"• **Planning & Due Diligence**: {profile['planning_notes']} For {comp_display}: {comp_prof['planning_notes']}"
        )
        actions.append(ChatAction(label=f"Explore {dist_display} 3D Map", action_type="navigate", target="prepare.html"))
        actions.append(ChatAction(label=f"Switch Location to {comp_display}", action_type="location", target=comp_display))
        suggested = [f"What are building rules in {dist_display}?", f"Show complaints in {dist_display}"]
        return ChatResponse(
            reply=reply,
            actions=actions,
            source_title="Copernicus DEM & Tamil Nadu Water Resources Department",
            source_url="https://bhuvan.nrsc.gov.in/",
            suggested_questions=suggested
        )

    # 2. Land Assessment & Due Diligence Explanation (e.g. "explain my land assessment", "what is elevation vs slope")
    if any(k in q for k in ["elevation", "slope", "difference", "gradient", "assess", "matrix", "readiness", "due diligence"]):
        if any(k in q for k in ["difference", "slope", "elevation"]):
            reply = (
                "**Elevation vs. Terrain Slope** explained simply:\n\n"
                "• **Elevation** is the height of your land above mean sea level (AMSL). For example, low-lying coastal land in Chennai may be only 6 meters AMSL, while Coimbatore is around 420 meters.\n\n"
                "• **Slope** measures the steepness or tilt of the ground. A flat plot has nearly 0% slope, while a hillside plot in the Nilgiris might have a 25% or steeper slope.\n\n"
                "**Why both matter in SOLUM:** A low elevation near a river creates ponding risks, whereas a steep slope on a hill poses landslide or rapid runoff risks. Both are evaluated before recommending construction readiness."
            )
        elif context and (context.get("assessment") or context.get("last_assessment")):
            ass = context.get("assessment") or context.get("last_assessment")
            reply = (
                f"**Here is what your Land Assessment for {ass.get('address', 'your site')} means:**\n\n"
                f"• **Readiness Status**: **{ass.get('overall_readiness', 'Evaluated')}** — {ass.get('summary_note', '')}\n"
                f"• **Elevation**: {ass.get('elevation_m', 0)}m AMSL · **Slope**: {ass.get('slope_percent', 0)}%\n"
                f"• **Waterbody Proximity**: {ass.get('distance_to_water_m', 0)}m to the nearest water corridor.\n"
                f"• **Key Advice**: {ass.get('planning_considerations', 'Verify boundary setbacks and soil bearing test.')}\n\n"
                "Would you like advice on statutory CMDA / DTCP setbacks or a soil stability survey?"
            )
        else:
            reply = (
                "**Understanding Land Assessments in SOLUM:**\n\n"
                "Before purchasing or building on a plot, SOLUM evaluates four grounded layers:\n"
                "1. **Copernicus Elevation & Slope**: Determines whether water naturally flows away or stagnates on your plot.\n"
                "2. **India-WRIS Waterbody Buffer**: Checks whether your site falls within statutory 100m catchment or wetland preservation corridors.\n"
                "3. **Flood History**: Reviews historical monsoon waterlogging levels in your revenue district.\n"
                "4. **Soil & Seismic Zone**: Evaluates foundation requirements under National Building Code (NBC 2016).\n\n"
                "You can run an instant preliminary assessment in the **Report** section."
            )
        actions.append(ChatAction(label="Run a Land Assessment", action_type="navigate", target="report.html"))
        suggested = ["What is the 100m waterbody buffer?", f"What are common land risks in {dist_display}?"]
        return ChatResponse(
            reply=reply,
            actions=actions,
            source_title="SOLUM Geospatial Land Intelligence & NBC 2016",
            source_url="https://bhuvan.nrsc.gov.in/",
            suggested_questions=suggested
        )

    # 3. Complaints & Civic Issues (e.g. "how do I report a damaged pole", "show complaints in my locality")
    if any(k in q for k in ["complaint", "report a", "damaged pole", "wire", "pothole", "problem", "ticket", "resolve"]):
        try:
            local_issues = list_issues(district=dist_display)
        except Exception:
            local_issues = []
            
        count = len(local_issues)
        open_count = sum(1 for i in local_issues if i.status != "Resolved")
        
        if "how do i report" in q or "report a" in q:
            reply = (
                f"**How to report civic hazards in {dist_display}:**\n\n"
                "1. Click the **'Raise a Complaint'** button below or in the navigation bar.\n"
                "2. Choose the hazard category (e.g., *Electricity* for fallen wires, *Drainage* for waterlogging, *Roads* for tree obstructions).\n"
                "3. Enter the landmark and describe who is affected.\n"
                "4. Optionally attach up to 3 photographs of the damage.\n"
                "5. Upon submission, SOLUM assigns an immutable ticket ID (e.g., `SLM-XXXXXXX`) and pins the coordinates directly to the 3D map for municipal triage."
            )
            actions.append(ChatAction(label="Raise a Complaint Now", action_type="action", target="complaint"))
        else:
            reply = (
                f"**Current Civic Records in {dist_display}:**\n\n"
                f"• There are currently **{count} registered records** in {dist_display} (**{open_count} open**, {count - open_count} resolved).\n"
                f"• Common reported categories include drainage desilting, road repairs, and electrical feeder protection.\n\n"
                f"All records are tracked transparently in the **Resolve** workspace with progress percentages, assigned teams, and field milestones."
            )
            actions.append(ChatAction(label=f"View {dist_display} Resolve Board", action_type="navigate", target="resolve.html"))
            actions.append(ChatAction(label="Raise a Complaint", action_type="action", target="complaint"))
            
        suggested = [f"What are the common land risks in {dist_display}?", "What should I pack in an emergency bag?"]
        return ChatResponse(
            reply=reply,
            actions=actions,
            source_title="SOLUM Municipal Issue Tracking & TANGEDCO Protocols",
            source_url="https://chennaicorporation.gov.in/",
            suggested_questions=suggested
        )

    # 4. District-Specific Land Risks & Environmental Conditions
    if any(k in q for k in ["risk", "condition", "flood", "hazard", "terrain", "weather", "about"]) and any(d in q for d in TN_DISTRICT_PROFILES.keys()) or ("what about" in q or "tell me about" in q):
        reply = (
            f"**Land & Environmental Conditions in {dist_display}:**\n\n"
            f"• **Topography & Elevation**: {profile['elevation']}.\n"
            f"• **Key Hydrological Corridors**: {profile['water_corridors']}.\n"
            f"• **Main Environmental Risks**: {profile['primary_risks']}.\n"
            f"• **Civic & Builder Recommendations**: {profile['planning_notes']}\n\n"
            f"You can explore realistic 3D elevation contours and run simulated rainfall and drainage scenarios on the **Prepare** map."
        )
        actions.append(ChatAction(label=f"Explore {dist_display} 3D Scenario", action_type="navigate", target="prepare.html"))
        actions.append(ChatAction(label=f"Check Land Due Diligence", action_type="navigate", target="report.html"))
        suggested = [f"Compare {dist_display} with Chennai", f"Show complaints in {dist_display}"]
        return ChatResponse(
            reply=reply,
            actions=actions,
            source_title="Copernicus DEM & Tamil Nadu State Disaster Management Authority",
            source_url="https://bhuvan.nrsc.gov.in/",
            suggested_questions=suggested
        )

    # 5. Emergency Preparedness & Supply Checklist
    if any(k in q for k in ["pack", "food", "grocery", "bag", "suppl", "water", "kit", "battery", "torch", "medic"]):
        reply = (
            "**Emergency Household Supply Kit (IMD & NDMA Standards):**\n\n"
            "• **Water & Food**: 3-day supply of drinking water (3–4 liters/person/day) and ready-to-eat non-perishable food.\n"
            "• **First-Aid & Medicine**: Prescribed medicines for at least 7 days, antiseptic wash, band-aids, ORS packets, and basic fever/pain medication.\n"
            "• **Power & Lighting**: Heavy-duty waterproof torch, extra batteries, and fully charged power banks for mobile phones.\n"
            "• **Documents**: Aadhaar cards, property papers, insurance, and medical records sealed in watertight plastic pouches.\n"
            "• **Special Needs**: Infant food, senior citizen necessities, and emergency whistle for distress signaling."
        )
        actions.append(ChatAction(label="Open Household Checklist", action_type="navigate", target="prepare.html"))
        suggested = ["Which routes are safe during floods?", "How do I report a damaged pole?"]
        return ChatResponse(
            reply=reply,
            actions=actions,
            source_title="IMD Chennai & NDMA Floods Dos & Don'ts",
            source_url="https://mausam.imd.gov.in/chennai/mcdata/dos%26donts.pdf",
            suggested_questions=suggested
        )

    # 6. Evacuation & Movement Safety
    if any(k in q for k in ["route", "road", "shelter", "evacuat", "path", "safe"]):
        reply = (
            "**Evacuation & Movement Advisory:**\n\n"
            "• **Never walk or drive through moving water**: Just 15 cm of flowing water can sweep an adult off their feet, and 30 cm will float most passenger cars.\n"
            "• **Submerged hazards**: Floodwater conceals missing manhole lids, open drainage channels, sharp construction debris, and fallen electrical lines.\n"
            "• **Follow verified authorities**: SOLUM displays modeled scenario simulations, not real-time road closures. Always follow designated evacuation routes announced by your local District Collectorate or Municipal Corporation."
        )
        actions.append(ChatAction(label="Explore 3D Terrain & Corridors", action_type="navigate", target="prepare.html"))
        suggested = ["What should I keep in my emergency bag?", f"What are land risks in {dist_display}?"]
        return ChatResponse(
            reply=reply,
            actions=actions,
            source_title="Tamil Nadu Disaster Management Authority (TNSDMA)",
            source_url="https://chennaicorporation.gov.in/",
            suggested_questions=suggested
        )

    # General Conversational Fallback
    reply = (
        f"Hello! I am **SOLUM AI**, your civic and geospatial guide for **{dist_display}** and across Tamil Nadu.\n\n"
        "Here are a few ways I can help:\n"
        f"• **Land Risks**: Ask me *'What are the common land risks in {dist_display}?'* or *'What is the difference between elevation and slope?'*\n"
        "• **Civic Issues**: Ask *'How do I report a damaged electric pole?'* or *'Show complaints in my area.'*\n"
        "• **Preparedness**: Ask *'What should I pack in an emergency bag?'* or *'How does the 3D flood scenario work?'*\n"
        "• **Comparisons**: Ask *'Compare Madurai with Chennai.'*\n\n"
        "What would you like to explore?"
    )
    actions.append(ChatAction(label=f"Explore {dist_display} in 3D", action_type="navigate", target="prepare.html"))
    actions.append(ChatAction(label="Check Land Due Diligence", action_type="navigate", target="report.html"))
    suggested = [
        f"What are common land risks in {dist_display}?",
        "What is the difference between elevation and slope?",
        "How do I report a damaged pole?",
        f"Compare {dist_display} with Coimbatore"
    ]
    return ChatResponse(
        reply=reply,
        actions=actions,
        source_title="SOLUM Decision Support System",
        source_url="https://bhuvan.nrsc.gov.in/",
        suggested_questions=suggested
    )

async def call_gemini_api_if_available(
    message: str,
    history: List[Any],
    context: Optional[Dict[str, Any]],
    location_name: str,
    district_key: str
) -> Optional[ChatResponse]:
    """Invokes Google Gemini API if a valid GEMINI_API_KEY is configured in the environment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    system_instruction = (
        "You are SOLUM AI, an intelligent, friendly, conversational, and context-aware assistant for SOLUM "
        "(a digital land intelligence and civic disaster preparedness platform for Tamil Nadu, India). "
        "Style: Friendly, clear, helpful, easy for everyday citizens to understand, scientifically grounded. "
        "Never fabricate official municipal claims, fake complaints, or operational disaster evacuation orders. "
        f"Current selected location: {location_name} (District: {district_key.capitalize()}). "
        f"Context data: {json.dumps(context or {})}. "
        "Keep answers concise, formatted with clear markdown bullet points."
    )

    contents = []
    if history:
        for turn in history[-6:]:
            role = "user" if getattr(turn, 'role', '') == "user" or turn.get("role") == "user" else "model"
            text = getattr(turn, 'content', '') or turn.get("content", "")
            contents.append({"role": role, "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 800}
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return ChatResponse(
                    reply=text,
                    actions=[ChatAction(label="Open Prepare in 3D", action_type="navigate", target="prepare.html")],
                    source_title="Google Gemini & SOLUM Geospatial Knowledge Base",
                    source_url="https://bhuvan.nrsc.gov.in/",
                    suggested_questions=["What is elevation vs slope?", "Show complaints in my area"]
                )
    except Exception:
        pass
    return None

async def generate_chat_response(request: ChatRequest) -> ChatResponse:
    loc_name = request.location.name if request.location and request.location.name else "Chennai"
    history = request.history or []
    context = {}
    if request.context:
        context = request.context.model_dump() if hasattr(request.context, 'model_dump') else request.context.dict()

    # Extract district scope
    district_key = extract_subject_district(
        request.message,
        history,
        request.location.district if request.location else loc_name
    )

    # 1. Try Gemini API if key is available
    gemini_resp = await call_gemini_api_if_available(
        request.message, history, context, loc_name, district_key
    )
    if gemini_resp:
        return gemini_resp

    # 2. Built-in Multi-Turn Conversational Reasoning Engine
    return generate_reasoning_reply(
        request.message, history, context, loc_name, district_key
    )
