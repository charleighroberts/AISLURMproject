from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Scenario, Simulation
from .services import refresh_responses, start_simulation


@login_required
def scenario_list(request):
    scenarios = Scenario.objects.filter(is_published=True)
    return render(request, "sims/scenario_list.html", {"scenarios": scenarios})


@login_required
@require_POST
def start(request, scenario_id):
    scenario = get_object_or_404(Scenario, pk=scenario_id, is_published=True)
    sim = start_simulation(request.user, scenario)
    return redirect("sims:simulation", sim_id=sim.pk)


def own_simulation(request, sim_id):
    return get_object_or_404(Simulation, pk=sim_id, user=request.user)


@login_required
def simulation(request, sim_id):
    sim = own_simulation(request, sim_id)
    refresh_responses(sim)
    return render(request, "sims/simulation.html", {"sim": sim, "responses": sim.agent_responses.all()})


@login_required
@require_POST
def submit(request, sim_id):
    sim = own_simulation(request, sim_id)
    text = request.POST.get("response", "").strip()
    if not text:
        messages.error(request, "Write a response before submitting.")
    elif not sim.is_submitted:
        # Locked once submitted, so seeing the AI answers can't change it.
        sim.user_response = text
        sim.submitted_at = timezone.now()
        sim.save(update_fields=["user_response", "submitted_at"])
    return redirect("sims:simulation", sim_id=sim.pk)


@login_required
def status(request, sim_id):
    sim = own_simulation(request, sim_id)
    refresh_responses(sim)
    agents = []
    for response in sim.agent_responses.all():
        agent = {"id": response.pk, "label": response.label, "status": response.status}
        # Agent text stays hidden until the user has submitted their own response.
        if sim.is_submitted and response.status == response.Status.DONE:
            agent["text"] = response.text
        agents.append(agent)
    return JsonResponse({"submitted": sim.is_submitted, "agents": agents})
