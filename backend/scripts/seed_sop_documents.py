"""
scripts/seed_sop_documents.py — Idempotent script to seed initial SOP documents.
"""
import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_maker
from models.sop_document import SOPDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INITIAL_SOPS = [
    {
        "title": "Standard Evacuation Procedure for Multi-Story Building Collapse",
        "category": "collapse",
        "content": "Assess structural stability before entry. Establish a command perimeter 100 meters away from the structure. Use listening devices and rescue dogs for initial search. Do not use heavy machinery until the exact locations of trapped victims are confirmed. Shore up critical load-bearing walls immediately.",
        "source_url": "https://example.com/collapse-sop"
    },
    {
        "title": "Urban Flood Response and Swift Water Rescue",
        "category": "flood",
        "content": "Identify the primary source of flooding and predicted crest times. Deploy swift water rescue teams only with PFDs and tethered boats. Cut main power to submerged neighborhoods. Prioritize the evacuation of ground-floor trapped residents before rescuing stranded individuals on rooftops.",
        "source_url": "https://example.com/flood-sop"
    },
    {
        "title": "Industrial Chemical Fire and Toxic Smoke Protocol",
        "category": "fire",
        "content": "Evacuate a 2-mile radius downwind of the fire immediately. Responders must use SCBA (Self-Contained Breathing Apparatus) gear. Do not use water if the chemical reaction is unknown; use Class D or appropriate foam suppressants. Decontaminate all victims before hospital transport.",
        "source_url": "https://example.com/fire-sop"
    },
    {
        "title": "Mass Casualty Medical Triage (START Protocol)",
        "category": "medical",
        "content": "Use the Simple Triage and Rapid Treatment (START) method. Categorize patients: RED (Immediate, respirations > 30, no radial pulse, or unable to follow commands), YELLOW (Delayed, serious but stable), GREEN (Minor, walking wounded), BLACK (Deceased/Expectant). Transport REDs first.",
        "source_url": "https://example.com/medical-sop"
    },
    {
        "title": "Wildfire Containment and Residential Evacuation",
        "category": "fire",
        "content": "Establish a defensible space boundary. Issue Level 3 'Go Now' evacuation orders via emergency broadcast for areas in the immediate path. Use aerial water drops to protect critical infrastructure. Ground teams must maintain two escape routes at all times.",
        "source_url": "https://example.com/wildfire-sop"
    },
    {
        "title": "Critical Infrastructure Failure (Power/Water)",
        "category": "other",
        "content": "Deploy backup generators to hospitals and emergency response centers first. Distribute bottled water at predetermined staging areas (schools, stadiums). Issue a boil water advisory immediately if water pressure drops below 20 psi.",
        "source_url": "https://example.com/infrastructure-sop"
    }
]

async def seed_sops():
    async with async_session_maker() as db:
        logger.info("Checking for existing SOP documents...")
        
        for sop_data in INITIAL_SOPS:
            # Check if exists by title
            stmt = select(SOPDocument).where(SOPDocument.title == sop_data["title"])
            result = await db.execute(stmt)
            existing = result.scalars().first()
            
            if existing:
                logger.info("SOP Document already exists: '%s'", sop_data["title"])
                # Update content if needed (upsert behavior)
                existing.content = sop_data["content"]
                existing.category = sop_data["category"]
                existing.source_url = sop_data["source_url"]
            else:
                logger.info("Inserting new SOP Document: '%s'", sop_data["title"])
                new_sop = SOPDocument(**sop_data)
                db.add(new_sop)
                
        await db.commit()
        logger.info("SOP seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_sops())
