"""
services/gemini_service.py — Google Gemini AI integration.
Provides triage classification and disaster report summarisation.
API key comes exclusively from GEMINI_API_KEY environment variable.
"""
import logging

from google import genai

from core.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()
_client = genai.Client(api_key=_settings.GEMINI_API_KEY)


# ── Triage Classification ─────────────────────────────────────────────────────
TRIAGE_SYSTEM_PROMPT = """
You are an emergency medical triage assistant trained on the START (Simple Triage
and Rapid Treatment) protocol. Based on the patient's symptoms and vital signs,
classify them into ONE of these categories:
- red    : Immediate life-threatening — needs treatment within minutes
- yellow : Delayed — serious but stable for 30–60 min
- green  : Minor — can wait or self-care
- black  : Expectant/Deceased — unsurvivable or no pulse/breathing

Respond ONLY with a JSON object:
{
  "triage_color": "<red|yellow|green|black>",
  "confidence": "<high|medium|low>",
  "recommendation": "<one-sentence action recommendation>"
}
Do not include markdown, explanation, or any other text.
""".strip()


async def classify_triage(symptoms: str, vital_signs: str | None = None) -> dict:
    """
    Use Gemini to classify triage severity from symptoms and vital signs.
    Returns a dict with keys: triage_color, confidence, recommendation.
    Falls back to 'yellow / low confidence' on any API error.
    """
    patient_info = f"Symptoms: {symptoms}"
    if vital_signs:
        patient_info += f"\nVital signs: {vital_signs}"

    prompt = f"{TRIAGE_SYSTEM_PROMPT}\n\nPatient info:\n{patient_info}"

    try:
        response = await _client.aio.models.generate_content(
            model=_settings.GEMINI_MODEL,
            contents=prompt
        )
        import json
        result = json.loads(response.text.strip())
        # Validate keys
        assert result.get("triage_color") in {"red", "yellow", "green", "black"}
        return result
    except Exception as exc:
        logger.warning("Gemini triage classification failed: %s", exc)
        return {
            "triage_color": "yellow",
            "confidence": "low",
            "recommendation": "Manual assessment required — AI classification unavailable.",
        }


# ── Report Summarisation ──────────────────────────────────────────────────────
SUMMARY_SYSTEM_PROMPT = """
You are an emergency management assistant. Summarise the following disaster report
in 2–3 concise sentences for use in an operational dashboard. Highlight:
- What type of disaster occurred
- Current severity and affected population
- Most urgent action needed

Return ONLY the summary text — no bullet points, no headings.
""".strip()


async def summarise_report(title: str, description: str, disaster_type: str, severity: str) -> str:
    """
    Generate a short operational summary of a disaster report using Gemini.
    Returns the summary string, or a generic fallback on error.
    """
    prompt = (
        f"{SUMMARY_SYSTEM_PROMPT}\n\n"
        f"Title: {title}\n"
        f"Type: {disaster_type}\n"
        f"Severity: {severity}\n"
        f"Description: {description}"
    )

    try:
        response = await _client.aio.models.generate_content(
            model=_settings.GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini summarisation failed: %s", exc)
        return f"{disaster_type.capitalize()} incident reported. Severity: {severity}. Manual review required."


# ── Report Severity Extraction ────────────────────────────────────────────────
REPORT_SEVERITY_PROMPT = """
Analyze the following emergency report and extract structured severity data.
You must return exactly ONE valid JSON object with NO markdown formatting, NO extra text.
The JSON must contain exactly these fields:
{
  "injury_count": <integer, estimate total injured. default 0>,
  "structural_damage": <boolean, true if buildings/infrastructure damaged>,
  "disaster_type": "<string, one of: fire, flood, collapse, medical, other>",
  "people_trapped": <integer, estimate people trapped. default 0>,
  "confidence_score": <float between 0.0 and 1.0 representing your confidence>
}
""".strip()

async def extract_report_severity(title: str, description: str) -> dict:
    """
    Calls Gemini to extract severity parameters from report text.
    Implements a 10s timeout and up to 2 retries with exponential backoff.
    """
    import asyncio
    import json
    
    prompt = f"{REPORT_SEVERITY_PROMPT}\n\nTitle: {title}\nDescription: {description}"
    
    max_retries = 2
    base_delay = 1.0

    for attempt in range(max_retries + 1):
        try:
            # 10s timeout per attempt
            response = await asyncio.wait_for(
                _client.aio.models.generate_content(
                    model=_settings.GEMINI_MODEL,
                    contents=prompt
                ),
                timeout=10.0
            )
            text = response.text.strip()
            # Strip markdown if present
            if text.startswith("```json"):
                text = text.replace("```json", "", 1)
            if text.endswith("```"):
                text = text[:-3]
            
            result = json.loads(text.strip())
            
            # Basic validation
            valid_types = {"fire", "flood", "collapse", "medical", "other"}
            if result.get("disaster_type") not in valid_types:
                result["disaster_type"] = "other"
                
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Gemini severity extraction timed out (attempt {attempt + 1}/{max_retries + 1})")
        except json.JSONDecodeError as exc:
            logger.warning(f"Gemini returned invalid JSON (attempt {attempt + 1}/{max_retries + 1}): {exc}")
        except Exception as exc:
            logger.warning(f"Gemini severity extraction failed (attempt {attempt + 1}/{max_retries + 1}): {exc}")
            
        if attempt < max_retries:
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
            
    # Raise exception if all retries fail so triage_service can trigger its fallback
    raise RuntimeError("Failed to extract report severity from Gemini after multiple attempts")
