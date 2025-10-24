import os
import json
from typing import Dict, Any, Optional
import asyncio
from google import genai
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Access your API key and initialize Gemini client at module load (fallback if not provided)
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


class Perception:
    """Perception module to interact with Gemini LLM for fact extraction.

    This class provides static async helpers so callers may use them via
    `Perception.extract_facts_with_gemini(query)` without instantiating.
    """

    @staticmethod
    async def generate_with_timeout(client, prompt: str, timeout: int = 10):
        """Generate content with a timeout using the provided Gemini client."""
        logger.info("Starting LLM generation...")
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt,
                    ),
                ),
                timeout=timeout,
            )
            logger.info("LLM generation completed")
            return response
        except asyncio.TimeoutError:
            logger.info("LLM generation timed out!")
            raise
        except Exception as e:
            logger.exception(f"Error in LLM generation: {e}")
            raise

    @staticmethod
    async def extract_facts_with_gemini(query: str, client_arg: Optional[Any] = None) -> Dict[str, Any]:
        """Extract structured facts from the query using Gemini.

        Args:
            query: The user's natural-language query.
            client_arg: Optional Gemini client to use; if omitted the module-level
                        client (created from GEMINI_API_KEY) will be used.

        Returns:
            A dict parsed from the LLM's JSON output, or an error dict.
        """
        prompt = f"""Analyze this query and extract key facts in JSON format:
- steps: List of distinct operations needed
- operations: Details about each operation
- parameters: Any specific values mentioned
- dependencies: What results are needed for which steps

Query: "{query}"

Example output:
{{
    "steps": ["ascii_conversion", "exponential_sum", "paint_operations", "email"],
    "operations": {{
        "ascii_conversion": "Convert INDIA to ASCII values",
        "exponential_sum": "Calculate sum of exponentials",
        "paint_operations": ["open_paint", "draw_rectangle", "add_text"],
        "email": "Send result via email"
    }},
    "parameters": {{
        "text": "INDIA",
        "rectangle": {{
            "x1": 607,
            "y1": 425,
            "x2": 940,
            "y2": 619
        }}
    }},
    "dependencies": {{
        "exponential_sum": "needs ascii_values",
        "add_text": "needs exponential_sum",
        "email": "needs exponential_sum"
    }}
}}"""

        use_client = client_arg if client_arg is not None else client
        if use_client is None:
            logger.error("No Gemini client available for Perception.extract_facts_with_gemini")
            return {"error": "No Gemini client configured"}

        response = await Perception.generate_with_timeout(use_client, prompt)
        if not response:
            return {"Failed to get response from Gemini"}

        try:
            return response.text
        except json.JSONDecodeError:
            logger.warning("Could not decode JSON from Gemini response; returning fallback structure")
            return {
                "steps": ["parse_text"],
                "operations": {"parse_text": query},
                "parameters": {},
                "dependencies": {},
            }