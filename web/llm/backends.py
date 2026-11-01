"""LLM backends.

The web app only talks to models through the LLMBackend interface, so the mock can be
swapped for Ollama (local) or SLURM (GPU cluster) without touching any views.
"""

import time
from dataclasses import dataclass

from django.conf import settings


@dataclass
class Result:
    text: str
    prompt_tokens: int
    completion_tokens: int


class LLMBackend:
    model_name = ""

    def submit(self, prompt: str, side: str, stance: str) -> str:
        """Start generating a response in the background and return a job id."""
        raise NotImplementedError

    def status(self, job_id: str) -> str:
        """Return "queued", "running", "done" or "failed"."""
        raise NotImplementedError

    def result(self, job_id: str) -> Result:
        """Return the finished response. Only called once status() is "done"."""
        raise NotImplementedError


CANNED = {
    ("nato", "hawkish"): (
        "[Mock] NATO should respond firmly but without provocation: move additional rotational forces "
        "to the region, raise readiness levels, and state publicly that any violation of allied territory "
        "will be met with a collective response. Military-to-military channels should stay open to avoid "
        "miscalculation."
    ),
    ("nato", "dovish"): (
        "[Mock] NATO should prioritize de-escalation: open a direct line to the adversary's leadership, "
        "propose talks through a neutral venue, and hold off on new deployments that could be read as "
        "provocation. Allies can be reassured through diplomatic statements and intelligence sharing."
    ),
    ("adversary", "hawkish"): (
        "[Mock] We will not be pressured. Our exercises will continue as planned, and any additional NATO "
        "deployments near our borders will be matched. The alliance should understand that our security "
        "interests are not open to negotiation."
    ),
    ("adversary", "dovish"): (
        "[Mock] We are prepared to reduce tensions. The current exercises will conclude on schedule, and we "
        "are open to a meeting on transparency measures, provided our own security concerns are taken "
        "seriously."
    ),
}


class MockBackend(LLMBackend):
    """Canned responses after a short delay, so the site can be built without GPUs.

    Everything it needs is encoded in the job id, so it works across server processes.
    """

    model_name = "mock"

    def submit(self, prompt, side, stance):
        return f"mock:{side}:{stance}:{time.time():.3f}:{len(prompt)}"

    def status(self, job_id):
        started = float(job_id.split(":")[3])
        return "done" if time.time() - started >= settings.MOCK_DELAY_SECONDS else "running"

    def result(self, job_id):
        _, side, stance, _, prompt_chars = job_id.split(":")
        text = CANNED[(side, stance)]
        # Roughly 4 characters per token for English text; real backends report exact counts.
        return Result(text=text, prompt_tokens=int(prompt_chars) // 4, completion_tokens=len(text) // 4)


def get_backend() -> LLMBackend:
    if settings.LLM_BACKEND == "mock":
        return MockBackend()
    raise ValueError(f"Unknown LLM_BACKEND {settings.LLM_BACKEND!r}; only 'mock' exists so far.")
