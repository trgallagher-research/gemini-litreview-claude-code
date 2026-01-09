"""
Translate plain-language context into structured light framing using Gemini 3 Flash.
"""

from google import genai
from google.genai import types


def translate_framing(context_raw: dict, api_key: str, model_name: str = "gemini-3-flash-preview") -> str:
    """
    Convert plain-language context to structured light framing.

    Args:
        context_raw: Dict with keys: description, population, constructs, focus
        api_key: Gemini API key
        model_name: Model to use for framing translation

    Returns:
        Structured framing paragraph
    """
    client = genai.Client(api_key=api_key)

    prompt = f"""You are helping structure context for an academic literature review extraction task.

The requester provided this plain-language description of their review:

---
WHAT THIS REVIEW IS ABOUT:
{context_raw.get('description', 'Not specified')}

TARGET POPULATION:
{context_raw.get('population', 'Not specified')}

KEY CONSTRUCTS OF INTEREST:
{context_raw.get('constructs', 'Not specified')}

FOCUS AREA:
{context_raw.get('focus', 'Not specified')}
---

Rewrite this as a concise "light framing" paragraph (4-6 sentences) that:
1. States the review's focus clearly in the first sentence
2. Defines the target population precisely
3. Lists key constructs with brief operational definitions
4. Notes the application context

The framing should help an AI extraction model understand what to look for WITHOUT biasing it toward any particular findings or conclusions. Use neutral, descriptive language.

Output ONLY the framing paragraph, nothing else."""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=500
        )
    )

    return response.text.strip()


def create_fallback_framing(context_raw: dict) -> str:
    """Create simple framing without LLM when API unavailable or skipped."""
    return f"""This review examines {context_raw.get('description', 'the specified topic')}

Target population: {context_raw.get('population', 'the target population')}

Key constructs of interest: {context_raw.get('constructs', 'relevant constructs')}

The focus is on findings relevant to {context_raw.get('focus', 'the specified context')}."""
