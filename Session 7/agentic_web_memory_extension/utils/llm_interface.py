import os
from typing import List

import google.generativeai as genai
from dotenv import load_dotenv


class LLMInterface:
    """Wrapper around Gemini Flash 2.0 for generation and embeddings.

    Environment variables:
      - GOOGLE_API_KEY: API key for Google Generative AI
      - GEMINI_MODEL: generation model name (default: gemini-2.0-flash)
      - GEMINI_EMBED_MODEL: embedding model name (default: gemini-embedding-001)
    """

    def __init__(self) -> None:
        # Load .env from project root (two levels up from this file)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        env_path = os.path.join(base_dir, ".env")
        try:
            load_dotenv(env_path)
        except Exception:
            # Best-effort load; continue if not present
            raise RuntimeError("env file not found")
            

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Gemini_API_KEY is not set")
        genai.configure(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.embed_model_name = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")

    def embed_text(self, text: str) -> List[float]:
        """Return an embedding vector for the given text."""
        res = genai.embed_content(model=self.embed_model_name, content=text)
        return res["embedding"]  # type: ignore[index]

    def summarize(self, text: str) -> str:
        """Return a concise summary of the text."""
        prompt = (
            "Summarize the following webpage text in 1-2 sentences, capturing its key topics.\n\n"
            f"Text:\n{text[:10000]}"
        )
        model = genai.GenerativeModel(self.model_name)
        out = model.generate_content(prompt)
        return out.text.strip() if getattr(out, "text", None) else ""

    def reason(self, context: str) -> str:
        """Use the model for brief reasoning/classification/instructions."""
        model = genai.GenerativeModel(self.model_name)
        out = model.generate_content(context[:12000])
        return out.text.strip() if getattr(out, "text", None) else ""


