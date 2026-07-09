"""
Model-agnostic LLM client.

Three backends:
  - "mock"     : no API key needed. Returns deterministic, clearly-labelled placeholder
                 responses so the whole pipeline runs end-to-end and you can inspect the
                 data contracts and report format. NOT real reasoning.
  - "anthropic": uses the Anthropic Messages API (set ANTHROPIC_API_KEY).
  - "openai"   : uses the OpenAI Chat Completions API (set OPENAI_API_KEY).

Select via the QM_BACKEND environment variable, or pass backend= explicitly.
The agents only ever call client.complete(system, user) and expect text back, so
swapping models never touches agent code.
"""

from __future__ import annotations
import os
import json

# Default models per backend. Override with QM_MODEL.
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "mock": "mock-deterministic",
}


class LLMClient:
    def __init__(self, backend: str | None = None, model: str | None = None,
                 temperature: float = 0.2, max_tokens: int = 2000,
                 timeout: float | None = None):
        # Default: use Claude automatically if a key is present, otherwise mock (zero-config).
        if backend is None:
            backend = os.environ.get("QM_BACKEND")
        if backend is None:
            backend = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "mock"
        self.backend = backend
        self.model = model or os.environ.get("QM_MODEL", DEFAULT_MODELS[self.backend])
        self.temperature = temperature
        self.max_tokens = max_tokens
        # Prompt-cache accounting (anthropic backend), summed across all calls.
        self.cache_read_tokens = 0
        self.cache_write_tokens = 0
        self.uncached_input_tokens = 0
        # Without an explicit timeout, a request that drops mid-flight (e.g. a network
        # blip) can hang the SDK indefinitely instead of raising -- see incident where
        # a run sat idle for 2+ hours after a connection drop.
        self.timeout = timeout or float(os.environ.get("QM_TIMEOUT", "120"))
        self._init_backend()

    def _init_backend(self):
        if self.backend == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(timeout=self.timeout)  # reads ANTHROPIC_API_KEY
        elif self.backend == "openai":
            from openai import OpenAI
            self._client = OpenAI(timeout=self.timeout)  # reads OPENAI_API_KEY
        elif self.backend == "mock":
            from .mock_brain import MockBrain
            self._client = MockBrain()
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def complete(self, system: str, user: str) -> str:
        if self.backend == "anthropic":
            # Cache the system prompt. It carries the full knowledge base and is
            # byte-identical across every candidate for a given agent role, so after
            # the first write each reuse bills the KB tokens at ~0.1x instead of full
            # price (5-minute ephemeral TTL, refreshed on every read; the agent roles
            # recur well within that window during a batch). The per-candidate user
            # message stays uncached -- it is the volatile suffix. Prompts below the
            # model's minimum cacheable prefix simply don't cache, no error.
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=[{"type": "text", "text": system,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user}],
            )
            u = resp.usage
            self.cache_read_tokens += getattr(u, "cache_read_input_tokens", 0) or 0
            self.cache_write_tokens += getattr(u, "cache_creation_input_tokens", 0) or 0
            self.uncached_input_tokens += getattr(u, "input_tokens", 0) or 0
            return "".join(b.text for b in resp.content if b.type == "text")

        if self.backend == "openai":
            resp = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp.choices[0].message.content

        if self.backend == "mock":
            return self._client.complete(system, user)

    def complete_json(self, system: str, user: str) -> dict:
        """Call the model and parse a JSON object from its reply (strips code fences)."""
        raw = self.complete(system + "\n\nReturn ONLY a valid JSON object, no prose, no code fences.", user)
        return _parse_json(raw)


def _parse_json(raw: str) -> dict:
    txt = raw.strip()
    if txt.startswith("```"):
        txt = txt.split("```", 2)[1]
        if txt.lstrip().startswith("json"):
            txt = txt.lstrip()[4:]
    txt = txt.strip().strip("`").strip()
    # find the outermost JSON object if extra prose slipped in
    start, end = txt.find("{"), txt.rfind("}")
    if start != -1 and end != -1:
        txt = txt[start:end + 1]
    try:
        return json.loads(txt)
    except json.JSONDecodeError as e:
        return {"_parse_error": str(e), "_raw": raw}
