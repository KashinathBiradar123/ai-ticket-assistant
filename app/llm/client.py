import logging

import requests
from groq import Groq

from app.config import settings


logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self.provider = settings.llm_provider.lower().strip()

        if self.provider == "groq":
            if not settings.groq_api_key:
                raise ValueError("GROQ_API_KEY is not configured.")

            self.client = Groq(api_key=settings.groq_api_key)
            self.model = settings.groq_model

        elif self.provider == "ollama":
            self.base_url = settings.ollama_base_url.rstrip("/")
            self.model = settings.ollama_model

        else:
            raise ValueError(
                f"Unsupported LLM provider: {settings.llm_provider}"
            )

    def generate(self, prompt: str, system: str = "") -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if self.provider == "groq":
            messages = []

            if system.strip():
                messages.append(
                    {
                        "role": "system",
                        "content": system,
                    }
                )

            messages.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
            )

            content = response.choices[0].message.content

            if not content:
                raise RuntimeError("LLM returned an empty response.")

            return content.strip()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }

        if system.strip():
            payload["system"] = system

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()
        content = data.get("response", "")

        if not content:
            raise RuntimeError("LLM returned an empty response.")

        return content.strip()

    def is_available(self) -> bool:
        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": "Reply with OK."}
                    ],
                    temperature=0,
                    max_tokens=50,
                )
                content = response.choices[0].message.content
                return bool(content and content.strip())

            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )
            if not response.ok:
                return False

            models = response.json().get("models", [])
            return any(
                model.get("name") == self.model
                or model.get("name", "").startswith(f"{self.model}:")
                for model in models
            )

        except Exception as exc:
            logger.warning("LLM availability check failed: %s", exc)
            return False


llm_client = LLMClient()