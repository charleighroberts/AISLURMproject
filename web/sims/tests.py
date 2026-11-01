from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Scenario, Simulation


@override_settings(LLM_BACKEND="mock", MOCK_DELAY_SECONDS=0)
class SimulationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("a@dsu.edu", "a@dsu.edu")
        self.client.force_login(self.user)
        self.scenario = Scenario.objects.create(title="Test", background="Background", prompt="What now?")

    def start(self):
        self.client.post(reverse("sims:start", args=[self.scenario.pk]))
        return Simulation.objects.get(scenario=self.scenario)

    def poll(self, sim):
        return self.client.get(reverse("sims:status", args=[sim.pk])).json()

    def test_start_creates_four_personas(self):
        sim = self.start()
        labels = [r.label for r in sim.agent_responses.all()]
        self.assertEqual(labels, [
            "Slightly hawkish NATO", "Slightly dovish NATO",
            "Slightly hawkish Adversary", "Slightly dovish Adversary",
        ])

    def test_agent_text_hidden_until_user_submits(self):
        sim = self.start()
        self.assertTrue(all("text" not in agent for agent in self.poll(sim)["agents"]))
        self.client.post(reverse("sims:submit", args=[sim.pk]), {"response": "My answer"})
        self.assertTrue(all(agent["text"] for agent in self.poll(sim)["agents"]))

    def test_response_locked_after_submit(self):
        sim = self.start()
        self.client.post(reverse("sims:submit", args=[sim.pk]), {"response": "First"})
        self.client.post(reverse("sims:submit", args=[sim.pk]), {"response": "Second"})
        sim.refresh_from_db()
        self.assertEqual(sim.user_response, "First")

    def test_token_usage_recorded(self):
        sim = self.start()
        self.poll(sim)
        for response in sim.agent_responses.all():
            self.assertGreater(response.prompt_tokens, 0)
            self.assertGreater(response.completion_tokens, 0)

    def test_other_users_cannot_see_simulation(self):
        sim = self.start()
        other = get_user_model().objects.create_user("b@dsu.edu", "b@dsu.edu")
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("sims:simulation", args=[sim.pk])).status_code, 404)
