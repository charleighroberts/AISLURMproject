import logging

from django.utils import timezone

from llm.backends import get_backend
from llm.personas import build_prompt

from .models import AgentResponse, Simulation

logger = logging.getLogger(__name__)

Side = AgentResponse.Side
Stance = AgentResponse.Stance
Status = AgentResponse.Status

PERSONAS = [
    (Side.NATO, Stance.HAWKISH),
    (Side.NATO, Stance.DOVISH),
    (Side.ADVERSARY, Stance.HAWKISH),
    (Side.ADVERSARY, Stance.DOVISH),
]


def start_simulation(user, scenario):
    """Create the simulation and start all four agent jobs while the user reads the prompt."""
    sim = Simulation.objects.create(user=user, scenario=scenario)
    backend = get_backend()
    for side, stance in PERSONAS:
        response = AgentResponse(simulation=sim, side=side, stance=stance, model_name=backend.model_name)
        try:
            response.job_id = backend.submit(build_prompt(scenario, side, stance), side, stance)
        except Exception:
            logger.exception("Failed to submit %s %s job for simulation %s", stance, side, sim.pk)
            response.status = Status.FAILED
        response.save()
    return sim


def refresh_responses(sim):
    """Ask the backend about unfinished jobs and save any finished results.

    Page loads and status polling drive this for now; a background worker can take over later.
    """
    backend = get_backend()
    for response in sim.agent_responses.filter(status__in=[Status.QUEUED, Status.RUNNING]):
        try:
            status = backend.status(response.job_id)
            if status == Status.DONE:
                result = backend.result(response.job_id)
                response.text = result.text
                response.prompt_tokens = result.prompt_tokens
                response.completion_tokens = result.completion_tokens
                response.completed_at = timezone.now()
            response.status = status
        except Exception:
            logger.exception("Failed to refresh job %s", response.job_id)
            response.status = Status.FAILED
        response.save()
