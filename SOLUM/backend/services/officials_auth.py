import hmac
import hashlib
import json
import base64
import time
from typing import Dict, Any, Optional
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.models import OfficialLoginRequest, OfficialAuthResponse

SECRET_KEY = "SOLUM-TN-OFFICIALS-KEY-SECURE-2026"
TOKEN_VALIDITY_SECONDS = 86400 # 24 hours

OFFICIAL_CREDENTIALS = {
    "OFF-TN-01": {
        "passcode": "SOLUM-TN-2026",
        "name": "Thiru. K. Rajendran, IAS",
        "role": "State Disaster Commissioner",
        "district": "All-TN"
    },
    "OFF-CH-02": {
        "passcode": "SOLUM-TN-2026",
        "name": "Dr. S. Meenakshi",
        "role": "District coordination officer",
        "district": "Chennai"
    },
    "OFF-CB-03": {
        "passcode": "SOLUM-TN-2026",
        "name": "Er. P. Shanmugam",
        "role": "District coordination officer",
        "district": "Coimbatore"
    },
    "OFF-MD-04": {
        "passcode": "SOLUM-TN-2026",
        "name": "Tmt. A. Soundarya",
        "role": "District coordination officer",
        "district": "Madurai"
    },
    "OFF-SL-05": {
        "passcode": "SOLUM-TN-2026",
        "name": "Er. M. Venkatesh",
        "role": "District coordination officer",
        "district": "Salem"
    },
    "OFF-TR-06": {
        "passcode": "SOLUM-TN-2026",
        "name": "Tmt. R. Revathi",
        "role": "District coordination officer",
        "district": "Tiruchirappalli"
    },
    "OFF-NL-07": {
        "passcode": "SOLUM-TN-2026",
        "name": "Er. K. Sivakumar",
        "role": "District coordination officer",
        "district": "Nilgiris"
    },
    "OFF-FIELD-08": {
        "passcode": "SOLUM-TN-2026",
        "name": "Inspector G. Murugan",
        "role": "Infrastructure repair lead",
        "district": "All-TN"
    },
    "OFF-RESCUE-09": {
        "passcode": "SOLUM-TN-2026",
        "name": "Capt. D. Anbarasan",
        "role": "Rescue team coordinator",
        "district": "All-TN"
    }
}

def create_official_token(official_id: str, role: str, district: str, name: str) -> str:
    payload = {
        "oid": official_id,
        "name": name,
        "role": role,
        "district": district,
        "exp": int(time.time()) + TOKEN_VALIDITY_SECONDS
    }
    raw = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    b64_payload = base64.urlsafe_b64encode(raw).decode('utf-8').rstrip('=')
    sig = hmac.new(SECRET_KEY.encode('utf-8'), b64_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}"

def verify_official_token(token: str) -> Dict[str, Any]:
    if not token or "." not in token:
        raise HTTPException(status_code=401, detail="Missing or malformed official authorization token")
    parts = token.split(".")
    if len(parts) != 2:
        raise HTTPException(status_code=401, detail="Invalid authorization token structure")
    b64_payload, sig = parts
    expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), b64_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(status_code=401, detail="Official token signature verification failed")
    
    pad = len(b64_payload) % 4
    if pad:
        b64_payload += "=" * (4 - pad)
    try:
        payload = json.loads(base64.urlsafe_b64decode(b64_payload.encode('utf-8')).decode('utf-8'))
    except Exception:
        raise HTTPException(status_code=401, detail="Malformed token payload")
        
    if payload.get("exp", 0) < time.time():
        raise HTTPException(status_code=401, detail="Official session has expired. Please log in again.")
    return payload

def authenticate_official(req: OfficialLoginRequest) -> OfficialAuthResponse:
    oid = req.official_id.strip().upper()
    passcode = req.passcode.strip()
    
    # Check registered official
    if oid in OFFICIAL_CREDENTIALS:
        cred = OFFICIAL_CREDENTIALS[oid]
        if cred["passcode"] != passcode:
            raise HTTPException(status_code=401, detail="Invalid official passcode.")
        role = cred["role"]
        district = cred["district"]
        name = cred["name"]
    elif passcode == "SOLUM-TN-2026":
        # Dynamic official login
        role = req.role or "District coordination officer"
        district = req.district or "Chennai"
        name = f"Official {oid}"
    else:
        raise HTTPException(status_code=401, detail="Invalid official ID or passcode.")
        
    token = create_official_token(oid, role, district, name)
    exp_iso = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() + TOKEN_VALIDITY_SECONDS))
    return OfficialAuthResponse(
        token=token,
        official_id=oid,
        name=name,
        role=role,
        district=district,
        expires_at=exp_iso
    )

def check_official_jurisdiction(official_payload: Dict[str, Any], target_district: Optional[str]) -> bool:
    """Returns True if the official is authorized to manage complaints in target_district."""
    off_dist = official_payload.get("district", "Chennai")
    if off_dist in ("All-TN", "State Disaster Management", "Tamil Nadu"):
        return True
    if not target_district:
        return True
    return off_dist.lower() == target_district.lower()

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_official(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Dict[str, Any]:
    # Check Bearer token first
    token = None
    if creds and creds.credentials:
        token = creds.credentials
    elif request.headers.get("X-Official-Token"):
        token = request.headers.get("X-Official-Token")
    elif request.query_params.get("token"):
        token = request.query_params.get("token")
        
    if not token:
        raise HTTPException(status_code=401, detail="Official authentication required. Please log in to Officials Access.")
    return verify_official_token(token)
