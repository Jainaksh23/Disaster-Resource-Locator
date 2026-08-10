"""
scripts/seed_demo_data.py — Seed the Neon production DB with demo data.

Idempotent: uses the record title/name as a dedup key so re-runs
never create duplicates.

Usage (from backend/):
    python ../scripts/seed_demo_data.py
    # or from repo root:
    python scripts/seed_demo_data.py
"""
import asyncio
import os
import ssl
import sys
import urllib.parse
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── Make sure `backend/` is on sys.path so we can import .env via dotenv ──
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR / ".env")

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Import ORM models (they register on Base.metadata)
# ---------------------------------------------------------------------------
from core.database import Base
from models.resource import Resource
from models.emergency_report import EmergencyReport
from models.user import User
from core.auth import get_password_hash


# ---------------------------------------------------------------------------
# Engine helper (same sslmode-stripping logic as core/database.py)
# ---------------------------------------------------------------------------
def _make_engine():
    db_url = os.environ["DATABASE_URL"]
    connect_args: dict = {}

    parsed = urllib.parse.urlparse(db_url)
    if parsed.query:
        params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        ssl_mode = params.pop("sslmode", [None])[0]
        new_query = urllib.parse.urlencode({k: v[0] for k, v in params.items()})
        db_url = urllib.parse.urlunparse(parsed._replace(query=new_query))

        if ssl_mode in ("require", "verify-ca", "verify-full", "prefer"):
            ctx = ssl.create_default_context()
            if ssl_mode in ("require", "prefer"):
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ctx

    # Neon free-tier needs SSL even if sslmode wasn't in the URL
    if not connect_args.get("ssl"):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx

    return create_async_engine(db_url, connect_args=connect_args, echo=False)


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------
RESOURCES = [
    {
        "name": "AIIMS Trauma Centre",
        "resource_type": "hospital",
        "capacity": 200,
        "status": "available",
        "location_name": "AIIMS, Ansari Nagar, New Delhi",
        "latitude": 28.5672,
        "longitude": 77.2100,
        "contact": "+91-11-26588500",
    },
    {
        "name": "Safdarjung Hospital",
        "resource_type": "hospital",
        "capacity": 150,
        "status": "available",
        "location_name": "Safdarjung Hospital, Ring Road, New Delhi",
        "latitude": 28.5685,
        "longitude": 77.2066,
        "contact": "+91-11-26707437",
    },
    {
        "name": "GTB Hospital Blood Bank",
        "resource_type": "bloodbank",
        "capacity": 500,
        "status": "available",
        "location_name": "GTB Hospital, Dilshad Garden, Delhi",
        "latitude": 28.6862,
        "longitude": 77.3152,
        "contact": "+91-11-22586262",
    },
    {
        "name": "Rotary Blood Bank",
        "resource_type": "bloodbank",
        "capacity": 350,
        "status": "available",
        "location_name": "56-57, Tughlakabad Institutional Area, New Delhi",
        "latitude": 28.5134,
        "longitude": 77.2590,
        "contact": "+91-11-29956484",
    },
    {
        "name": "DDMA Relief Shelter - Yamuna Sports Complex",
        "resource_type": "shelter",
        "capacity": 1000,
        "status": "available",
        "location_name": "Yamuna Sports Complex, Surajmal Vihar, Delhi",
        "latitude": 28.6227,
        "longitude": 77.2980,
        "contact": "+91-11-23890000",
    },
    {
        "name": "Ramlila Maidan Emergency Shelter",
        "resource_type": "shelter",
        "capacity": 800,
        "status": "available",
        "location_name": "Ramlila Maidan, Ajmeri Gate, New Delhi",
        "latitude": 28.6389,
        "longitude": 77.2378,
        "contact": "+91-11-23890100",
    },
    {
        "name": "Gurdwara Bangla Sahib Langar & Shelter",
        "resource_type": "shelter",
        "capacity": 500,
        "status": "available",
        "location_name": "Gurdwara Bangla Sahib, Connaught Place, Delhi",
        "latitude": 28.6264,
        "longitude": 77.2091,
        "contact": "+91-11-23312580",
    },
    {
        "name": "SEEDS India (Sustainable Environment and Ecological Development Society)",
        "resource_type": "ngo",
        "capacity": 50,
        "status": "available",
        "location_name": "15-A, Institutional Area, Sector 4, R.K. Puram, New Delhi",
        "latitude": 28.5638,
        "longitude": 77.1764,
        "contact": "+91-11-26174272",
    },
    {
        "name": "Indian Red Cross Society - Delhi Branch",
        "resource_type": "ngo",
        "capacity": 100,
        "status": "available",
        "location_name": "Red Cross Bhawan, Golf Links, New Delhi",
        "latitude": 28.5924,
        "longitude": 77.2310,
        "contact": "+91-11-23711551",
    },
    {
        "name": "Max Super Specialty Hospital - Saket",
        "resource_type": "hospital",
        "capacity": 250,
        "status": "available",
        "location_name": "Max Hospital, Press Enclave Road, Saket, New Delhi",
        "latitude": 28.5276,
        "longitude": 77.2137,
        "contact": "+91-11-26515050",
    },
    {
        "name": "Lok Nayak Jai Prakash (LNJP) Hospital",
        "resource_type": "hospital",
        "capacity": 1000,
        "status": "available",
        "location_name": "Jawaharlal Nehru Marg, New Delhi",
        "latitude": 28.6385,
        "longitude": 77.2384,
        "contact": "+91-11-23232400",
    },
    {
        "name": "Rajiv Gandhi Super Speciality Hospital",
        "resource_type": "hospital",
        "capacity": 300,
        "status": "available",
        "location_name": "Taharpur Road, Dilshad Garden, Delhi",
        "latitude": 28.6836,
        "longitude": 77.3090,
        "contact": "+91-11-22890604",
    },
    {
        "name": "Delhi Police Headquarters",
        "resource_type": "police_station",
        "capacity": 100,
        "status": "available",
        "location_name": "Jai Singh Road, New Delhi",
        "latitude": 28.6253,
        "longitude": 77.2104,
        "contact": "112",
    },
    {
        "name": "Hauz Khas Police Station",
        "resource_type": "police_station",
        "capacity": 30,
        "status": "available",
        "location_name": "Hauz Khas, New Delhi",
        "latitude": 28.5471,
        "longitude": 77.2007,
        "contact": "+91-11-26862555",
    },
    {
        "name": "Connaught Place Fire Station",
        "resource_type": "fire_station",
        "capacity": 5,
        "status": "available",
        "location_name": "Connaught Place, New Delhi",
        "latitude": 28.6321,
        "longitude": 77.2185,
        "contact": "101",
    },
    {
        "name": "Okhla Fire Station",
        "resource_type": "fire_station",
        "capacity": 6,
        "status": "available",
        "location_name": "Okhla Industrial Estate, New Delhi",
        "latitude": 28.5268,
        "longitude": 77.2750,
        "contact": "+91-11-26812222",
    },
    {
        "name": "Khalsa Help International",
        "resource_type": "ngo",
        "capacity": 150,
        "status": "available",
        "location_name": "Chandni Chowk, New Delhi",
        "latitude": 28.6559,
        "longitude": 77.2321,
        "contact": "+91-9811122334",
    },
    {
        "name": "Goonj Relief Center",
        "resource_type": "ngo",
        "capacity": 80,
        "status": "available",
        "location_name": "Sarita Vihar, New Delhi",
        "latitude": 28.5303,
        "longitude": 77.2778,
        "contact": "+91-11-41401216",
    },
    {
        "name": "Lions Blood Bank",
        "resource_type": "bloodbank",
        "capacity": 250,
        "status": "available",
        "location_name": "Shalimar Bagh, Delhi",
        "latitude": 28.7180,
        "longitude": 77.1472,
        "contact": "+91-11-47000000",
    },
    {
        "name": "Vasant Kunj Community Shelter",
        "resource_type": "shelter",
        "capacity": 300,
        "status": "available",
        "location_name": "Sector C, Vasant Kunj, New Delhi",
        "latitude": 28.5293,
        "longitude": 77.1537,
        "contact": "+91-11-26135555",
    },
    {
        "name": "Sir Ganga Ram Hospital",
        "resource_type": "hospital",
        "capacity": 400,
        "status": "available",
        "location_name": "Rajinder Nagar, New Delhi",
        "latitude": 28.6394,
        "longitude": 77.1895,
        "contact": "+91-11-25750000",
    },
    {
        "name": "Noida Sector 18 Police Station",
        "resource_type": "police_station",
        "capacity": 40,
        "status": "available",
        "location_name": "Sector 18, Noida",
        "latitude": 28.5707,
        "longitude": 77.3271,
        "contact": "+91-120-2510000",
    },
]

REPORTS = [
    {
        "title": "Major fire at Chandni Chowk market",
        "description": "Large fire has broken out in the cloth market area near Chandni Chowk metro station. Multiple shops engulfed. Fire tenders requested urgently.",
        "category": "fire",
        "severity_score": 5,
        "status": "active",
        "location_name": "Chandni Chowk Market, Old Delhi",
        "latitude": 28.6506,
        "longitude": 77.2302,
    },
    {
        "title": "Yamuna flood warning - Mayur Vihar low-lying area",
        "description": "Water level crossing danger mark near Mayur Vihar Phase 1. Several jhuggi clusters at risk. Evacuation teams needed immediately.",
        "category": "flood",
        "severity_score": 4,
        "status": "active",
        "location_name": "Yamuna Bank, Mayur Vihar Phase 1, Delhi",
        "latitude": 28.6075,
        "longitude": 77.2961,
    },
    {
        "title": "Building collapse in Bhajanpura",
        "description": "Three-storey residential building partially collapsed in Bhajanpura area. At least 10 people feared trapped under debris. NDRF team requested.",
        "category": "collapse",
        "severity_score": 5,
        "status": "active",
        "location_name": "Bhajanpura, North East Delhi",
        "latitude": 28.6938,
        "longitude": 77.2710,
    },
    {
        "title": "Medical emergency at Connaught Place metro",
        "description": "Mass casualty event at Rajiv Chowk metro station due to stampede. Multiple injured people requiring ambulance and first aid.",
        "category": "medical",
        "severity_score": 4,
        "status": "contained",
        "location_name": "Rajiv Chowk Metro Station, Connaught Place",
        "latitude": 28.6328,
        "longitude": 77.2197,
    },
    {
        "title": "Gas leak at Okhla Industrial Area",
        "description": "Suspected ammonia gas leak from a cold storage unit in Okhla Phase 2. Residents reporting breathing difficulty. HazMat team needed.",
        "category": "other",
        "severity_score": 3,
        "status": "active",
        "location_name": "Okhla Industrial Area Phase 2, Delhi",
        "latitude": 28.5308,
        "longitude": 77.2716,
    },
    {
        "title": "Flood water logging at Minto Bridge",
        "description": "Heavy waterlogging at Minto Bridge underpass. Several vehicles stuck. Traffic diverted. Pumping operations underway.",
        "category": "flood",
        "severity_score": 2,
        "status": "resolved",
        "location_name": "Minto Bridge, Connaught Place, New Delhi",
        "latitude": 28.6271,
        "longitude": 77.2263,
    },
    {
        "title": "Fire in slum cluster near Sarai Rohilla",
        "description": "Fire broke out in a slum cluster near Sarai Rohilla railway station. Around 30 shanties gutted. No casualties reported so far. Relief camp being set up.",
        "category": "fire",
        "severity_score": 3,
        "status": "contained",
        "location_name": "Sarai Rohilla, Central Delhi",
        "latitude": 28.6644,
        "longitude": 77.1853,
    },
    {
        "title": "Road accident with medical injuries on NH-24",
        "description": "Multi-vehicle pile-up on NH-24 near Ghazipur border. At least 5 critically injured. Ambulances dispatched from nearby hospitals.",
        "category": "medical",
        "severity_score": 4,
        "status": "contained",
        "location_name": "NH-24, Ghazipur Border, Delhi",
        "latitude": 28.6218,
        "longitude": 77.3228,
    },
]

USERS = [
    {
        "email": "admin@disaster.dev",
        "full_name": "Admin User",
        "password": "admin1234",
        "role": "admin",
    },
    {
        "email": "citizen@disaster.dev",
        "full_name": "Citizen User",
        "password": "citizen1234",
        "role": "citizen",
    },
]


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------
async def seed():
    engine = _make_engine()

    async with engine.begin() as conn:
        # Ensure tables exist (safe if already present)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # ── Resources ─────────────────────────────────────────────────────
        existing_resources = set(
            (await session.execute(select(Resource.name))).scalars().all()
        )
        new_resources = 0
        for r in RESOURCES:
            if r["name"] not in existing_resources:
                session.add(Resource(id=uuid.uuid4(), **r))
                new_resources += 1

        # ── Emergency Reports ─────────────────────────────────────────────
        existing_reports = set(
            (await session.execute(select(EmergencyReport.title))).scalars().all()
        )
        new_reports = 0
        for rp in REPORTS:
            if rp["title"] not in existing_reports:
                session.add(EmergencyReport(id=uuid.uuid4(), **rp))
                new_reports += 1

        # ── Users ─────────────────────────────────────────────────────────
        existing_users = set(
            (await session.execute(select(User.email))).scalars().all()
        )
        new_users = 0
        for u in USERS:
            if u["email"] not in existing_users:
                hashed_pw = get_password_hash(u.pop("password"))
                session.add(User(id=uuid.uuid4(), hashed_password=hashed_pw, **u))
                new_users += 1

        await session.commit()

    # ── Verify ────────────────────────────────────────────────────────────
    async with session_factory() as session:
        total_resources = (await session.execute(text("SELECT count(*) FROM resources"))).scalar()
        total_reports = (await session.execute(text("SELECT count(*) FROM emergency_reports"))).scalar()
        total_users = (await session.execute(text("SELECT count(*) FROM users"))).scalar()

    await engine.dispose()

    print("=" * 60)
    print("  SEED COMPLETE")
    print("=" * 60)
    print(f"  Resources  -> inserted {new_resources} new  |  total in DB: {total_resources}")
    print(f"  Reports    -> inserted {new_reports} new  |  total in DB: {total_reports}")
    print(f"  Users      -> inserted {new_users} new  |  total in DB: {total_users}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
