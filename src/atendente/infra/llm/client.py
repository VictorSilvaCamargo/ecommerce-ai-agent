from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


class LLMMessage(BaseModel):
    """Mensagem de entrada para o LLM."""

    model_config = ConfigDict(extra="ignore")

    role: str
    content: str


class LLMToolCall(BaseModel):
    """Chamada de ferramenta gerada pelo LLM."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Resposta estruturada do LLM."""

    model_config = ConfigDict(extra="ignore")

    content: str | None = None
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=lambda: {"total_tokens": 100})


class LLMClient(ABC):
    """Interface abstrata única para provedores de LLM."""

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Gera resposta ou chamada de ferramenta a partir de mensagens."""
        pass


class MockLLMClient(LLMClient):
    """Mock determinístico para execução de testes sem chamadas de rede."""

    def __init__(self, default_response: str = "Atendimento NovaLoja simulado.") -> None:
        self.default_response = default_response
        self._queue: list[LLMResponse] = []
        self.call_history: list[dict[str, Any]] = []

    def enqueue_response(self, response: LLMResponse) -> None:
        self._queue.append(response)

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        self.call_history.append(
            {
                "messages": [m.model_dump() for m in messages],
                "system_prompt": system_prompt,
                "tools": tools,
                "temperature": temperature,
            }
        )
        if self._queue:
            return self._queue.pop(0)

        return LLMResponse(
            content=self.default_response,
            usage={"prompt_tokens": 50, "completion_tokens": 50, "total_tokens": 100},
        )


class OpenAILLMClient(LLMClient):
    """Cliente para API OpenAI (chat/completions)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        formatted_messages: list[dict[str, str]] = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend([m.model_dump() for m in messages])

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]
        content = choice.get("content")
        tool_calls: list[LLMToolCall] = []

        if "tool_calls" in choice and choice["tool_calls"]:
            for tc in choice["tool_calls"]:
                tool_calls.append(
                    LLMToolCall(
                        id=tc.get("id", ""),
                        name=tc["function"]["name"],
                        arguments=tc["function"].get("arguments", {}),
                    )
                )

        usage = data.get("usage", {"total_tokens": 0})
        return LLMResponse(content=content, tool_calls=tool_calls, usage=usage)


class GeminiLLMClient(LLMClient):
    """Cliente para API Google Gemini (generativeLanguage)."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
    ) -> None:
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        contents: list[dict[str, Any]] = []
        for m in messages:
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        content = ""
        if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
            content = candidates[0]["content"]["parts"][0].get("text", "")

        return LLMResponse(content=content, usage={"total_tokens": 100})


class AnthropicLLMClient(LLMClient):
    """Cliente para API Anthropic Claude (messages)."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
    ) -> None:
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        formatted_messages = [
            {"role": "user" if m.role == "user" else "assistant", "content": m.content}
            for m in messages
        ]
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": 1024,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages", headers=headers, json=payload
            )
            resp.raise_for_status()
            data = resp.json()

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = {
            "input_tokens": data.get("usage", {}).get("input_tokens", 0),
            "output_tokens": data.get("usage", {}).get("output_tokens", 0),
            "total_tokens": data.get("usage", {}).get("input_tokens", 0)
            + data.get("usage", {}).get("output_tokens", 0),
        }
        return LLMResponse(content=content, usage=usage)
