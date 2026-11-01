from django.conf import settings
from django.db import models


class Scenario(models.Model):
    title = models.CharField(max_length=200)
    background = models.TextField(help_text="Context shown to the user before the question.")
    prompt = models.TextField(help_text="The question the user and the AI agents all respond to.")
    is_published = models.BooleanField(default=True, help_text="Unpublished scenarios are hidden from users.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Simulation(models.Model):
    """One user's attempt at a scenario."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="simulations")
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT, related_name="simulations")
    created_at = models.DateTimeField(auto_now_add=True)
    user_response = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.scenario}"

    @property
    def is_submitted(self):
        return self.submitted_at is not None


class AgentResponse(models.Model):
    """One AI persona's answer to the scenario prompt, generated in the background."""

    class Side(models.TextChoices):
        NATO = "nato", "NATO"
        ADVERSARY = "adversary", "Adversary"

    class Stance(models.TextChoices):
        HAWKISH = "hawkish", "Slightly hawkish"
        DOVISH = "dovish", "Slightly dovish"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    simulation = models.ForeignKey(Simulation, on_delete=models.CASCADE, related_name="agent_responses")
    side = models.CharField(max_length=20, choices=Side.choices)
    stance = models.CharField(max_length=20, choices=Stance.choices)
    job_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    model_name = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.label

    @property
    def label(self):
        return f"{self.get_stance_display()} {self.get_side_display()}"

    @property
    def is_pending(self):
        return self.status in (self.Status.QUEUED, self.Status.RUNNING)
