"""
services/triage_service.py — Rule-based severity weighting and AI extraction logic.
"""
import logging
import re
from typing import Any

from services.gemini_service import extract_report_severity

logger = logging.getLogger(__name__)

# ── Weights & Constants ───────────────────────────────────────────────────────
# Define how much each factor contributes to the 1-10 severity score.
# We'll normalize these weights so the maximum possible score maps to 10.
WEIGHT_INJURY = 0.4
WEIGHT_TRAPPED = 0.5
WEIGHT_STRUCTURAL = 0.3

# Base score just for a report being filed.
BASE_SCORE = 1.0


async def calculate_report_severity(title: str, description: str) -> dict[str, Any]:
    """
    Computes a 1-10 severity score for a disaster report.
    Returns: {
        "severity_score": int (1-10),
        "structured_data": dict (the extracted parameters),
        "raw_gemini_output": dict (the raw output from Gemini, or fallback info)
    }
    """
    raw_output: dict[str, Any] = {}
    structured: dict[str, Any] = {
        "injury_count": 0,
        "structural_damage": False,
        "disaster_type": "other",
        "people_trapped": 0,
        "confidence_score": 0.0,
    }

    try:
        raw_output = await extract_report_severity(title, description)
        
        # Merge raw output into structured data, ensuring types
        structured["injury_count"] = int(raw_output.get("injury_count", 0))
        structured["structural_damage"] = bool(raw_output.get("structural_damage", False))
        structured["disaster_type"] = str(raw_output.get("disaster_type", "other"))
        structured["people_trapped"] = int(raw_output.get("people_trapped", 0))
        structured["confidence_score"] = float(raw_output.get("confidence_score", 1.0))
        
    except Exception as exc:
        logger.error(f"Failed to use Gemini for report severity. Falling back to keyword matching: {exc}")
        structured = _fallback_keyword_extraction(title, description)
        raw_output = {"error": str(exc), "fallback_triggered": True}

    # ── Rule-Based Scoring Formula ────────────────────────────────────────────
    # Injury contribution: caps at 5 points (e.g., 50 injuries)
    injury_score = min(structured["injury_count"] * 0.1, 5.0) * WEIGHT_INJURY
    
    # Trapped contribution: heavily weighted, caps at 6 points (e.g., 20 trapped)
    trapped_score = min(structured["people_trapped"] * 0.3, 6.0) * WEIGHT_TRAPPED
    
    # Structural damage contribution: binary
    structural_score = 3.0 * WEIGHT_STRUCTURAL if structured["structural_damage"] else 0.0

    raw_score = BASE_SCORE + injury_score + trapped_score + structural_score
    
    # Normalize and clamp to 1-10 integer
    final_score = max(1, min(10, round(raw_score)))
    
    logger.info(
        f"Calculated severity: {final_score}/10 | "
        f"Base: {BASE_SCORE} | "
        f"Injuries ({structured['injury_count']})->{injury_score:.1f} | "
        f"Trapped ({structured['people_trapped']})->{trapped_score:.1f} | "
        f"Structural ({structured['structural_damage']})->{structural_score:.1f}"
    )

    return {
        "severity_score": final_score,
        "structured_data": structured,
        "raw_gemini_output": raw_output
    }


def _fallback_keyword_extraction(title: str, description: str) -> dict[str, Any]:
    """
    Simple keyword and regex matching fallback when AI fails.
    """
    text = (title + " " + description).lower()
    
    # Structural damage keywords
    structural = any(kw in text for kw in ["collapse", "destroy", "damage", "rubble", "crushed"])
    
    # Disaster type keywords
    disaster_type = "other"
    if any(kw in text for kw in ["fire", "burn", "smoke", "blaze"]):
        disaster_type = "fire"
    elif any(kw in text for kw in ["flood", "water", "drown", "submerge"]):
        disaster_type = "flood"
    elif any(kw in text for kw in ["medical", "sick", "disease"]):
        disaster_type = "medical"
    elif "collapse" in text or "earthquake" in text:
        disaster_type = "collapse"
        
    # Attempt to extract numbers near 'injur' or 'dead' or 'trapped'
    injury_count = 0
    trapped_count = 0
    
    # Look for patterns like "5 injured", "10 people trapped"
    injury_matches = re.findall(r'(\d+)\s+(?:people\s+)?(?:are\s+)?(?:injured|dead|hurt|casualties)', text)
    if injury_matches:
        injury_count = sum(int(m) for m in injury_matches)
        
    trapped_matches = re.findall(r'(\d+)\s+(?:people\s+)?(?:are\s+)?(?:trapped|stuck|missing)', text)
    if trapped_matches:
        trapped_count = sum(int(m) for m in trapped_matches)
        
    # If keywords exist but no numbers, assume at least 1
    if injury_count == 0 and any(kw in text for kw in ["injured", "dead", "casualties", "hurt"]):
        injury_count = 1
    if trapped_count == 0 and any(kw in text for kw in ["trapped", "stuck", "missing"]):
        trapped_count = 1
        
    return {
        "injury_count": injury_count,
        "structural_damage": structural,
        "disaster_type": disaster_type,
        "people_trapped": trapped_count,
        "confidence_score": 0.0,
    }
