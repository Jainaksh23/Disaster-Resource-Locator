"""
services/rag_service.py — Retrieval-Augmented Generation for SOP Documents.
"""
import json
import logging
from pathlib import Path

import faiss
import numpy as np
from google import genai

from core.config import get_settings
from models.sop_document import SOPDocument

logger = logging.getLogger(__name__)
settings = get_settings()

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "faiss"
INDEX_PATH = DATA_DIR / "sop.index"
MAPPING_PATH = DATA_DIR / "mapping.json"

_index: faiss.IndexFlatL2 | None = None
_mapping: dict[int, dict] | None = None


async def embed_text(text: str) -> list[float]:
    """Generates an embedding vector using Gemini API."""
    response = await _client.aio.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )
    return response.embeddings[0].values


async def init_rag() -> None:
    """Loads the FAISS index and mapping file into memory."""
    global _index, _mapping
    
    if not INDEX_PATH.exists() or not MAPPING_PATH.exists():
        logger.warning(
            "FAISS index or mapping file not found at %s. "
            "RAG features will be disabled until 'rebuild_faiss_index.py' is run.",
            DATA_DIR
        )
        return

    logger.info("Loading FAISS index from %s", INDEX_PATH)
    try:
        # Load the index
        _index = faiss.read_index(str(INDEX_PATH))
        
        # Load the mapping
        with open(MAPPING_PATH, "r", encoding="utf-8") as f:
            str_keys_mapping = json.load(f)
            # Convert JSON string keys back to int
            _mapping = {int(k): v for k, v in str_keys_mapping.items()}
            
        logger.info("Successfully loaded FAISS index with %d documents", _index.ntotal)
    except Exception as exc:
        logger.error("Failed to load FAISS index: %s", exc)
        _index = None
        _mapping = None


async def build_index(documents: list[SOPDocument]) -> None:
    """
    Computes embeddings for all SOP documents, builds a FAISS index, 
    and saves both the index and mapping to disk.
    """
    if not documents:
        logger.warning("No SOP documents provided to build_index.")
        return

    embeddings = []
    mapping = {}

    logger.info(f"Generating embeddings for {len(documents)} SOP documents...")
    for i, doc in enumerate(documents):
        text = f"{doc.title}\n{doc.category}\n{doc.content}"
        vec = await embed_text(text)
        embeddings.append(vec)
        
        mapping[i] = {
            "id": str(doc.id),
            "title": doc.title,
            "category": doc.category,
            "content": doc.content,
            "source_url": doc.source_url
        }

    # Convert to numpy array of float32 (FAISS requirement)
    embedding_matrix = np.array(embeddings).astype("float32")
    dimension = embedding_matrix.shape[1]

    logger.info(f"Building FAISS index (dimension: {dimension})...")
    # Using L2 distance for similarity
    index = faiss.IndexFlatL2(dimension)
    index.add(embedding_matrix)

    # Ensure directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save to disk
    faiss.write_index(index, str(INDEX_PATH))
    
    with open(MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
        
    logger.info("Successfully saved FAISS index and mapping to %s", DATA_DIR)

    # Hot reload into memory
    global _index, _mapping
    _index = index
    _mapping = mapping


async def query_index(query_text: str, top_k: int = 3) -> list[dict]:
    """
    Computes embedding for query_text and returns the top_k matching SOP documents.
    Returns empty list if RAG is not initialized.
    """
    if _index is None or _mapping is None:
        return []

    try:
        vec = await embed_text(query_text)
        # Reshape to 2D array: 1 query, D dimensions
        query_matrix = np.array([vec]).astype("float32")

        # Search index
        distances, indices = _index.search(query_matrix, top_k)
        
        results = []
        # distances and indices are 2D arrays: [n_queries][top_k]
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1: # FAISS returns -1 if there aren't enough items
                continue
                
            doc = _mapping[int(idx)]
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "category": doc["category"],
                "content": doc["content"], # Consider truncating content if it's too long
                "source_url": doc["source_url"],
                "_distance": float(dist)
            })
            
        return results
    except Exception as exc:
        logger.error("RAG query failed: %s", exc)
        return []
