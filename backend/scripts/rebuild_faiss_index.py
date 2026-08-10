"""
scripts/rebuild_faiss_index.py — Rebuild the FAISS index from the database.
"""
import asyncio
import logging
from sqlalchemy import select

from core.database import async_session_maker
from models.sop_document import SOPDocument
from services.rag_service import build_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def rebuild_index():
    async with async_session_maker() as db:
        logger.info("Fetching all SOP documents from the database...")
        stmt = select(SOPDocument)
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        if not documents:
            logger.warning("No SOP documents found in the database. Seeding might be required.")
            return
            
        logger.info("Found %d SOP documents. Initiating FAISS rebuild...", len(documents))
        await build_index(list(documents))
        
        logger.info("FAISS rebuild complete.")

if __name__ == "__main__":
    asyncio.run(rebuild_index())
