import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class LLMClient:
    """
    Centralized Groq client used by all ForgeAI LLM components.

    Responsibilities:
    - structured JSON generation
    - tool-calling conversations
    - model selection supplied by LLMRouter
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv(
            "GROQ_MODEL",
            "qwen/qwen3.8-27b",
        )

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=self.api_key
        )

    def generate(
        self,
        user_message: str,
        schema: dict[str, Any],
        schema_name: str = "forgeai_response",
        model: str | None = None,
        max_tokens: int = 1200,
    ) -> str:
        """
        Generate a structured JSON response.

        Used for:
        - architecture planning
        - impact analysis
        - other deterministic structured outputs
        """

        if not user_message.strip():
            raise ValueError(
                "LLM generation requires a non-empty prompt."
            )

        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            max_tokens=max_tokens,
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                },
            },
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "LLM returned an empty structured response."
            )

        return content

    def chat_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int = 4000,
    ):
        """
        Run a tool-calling conversation.

        The model decides whether to:
        - call a tool
        - call multiple tools
        - return a final response
        """

        if not messages:
            raise ValueError(
                "Tool-calling conversation requires messages."
            )

        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=max_tokens,
            temperature=0,
        )

        return response.choices[0].message