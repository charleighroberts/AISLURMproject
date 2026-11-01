from django.contrib import admin
from django.db.models import F, Sum

from .models import AgentResponse, Scenario, Simulation


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ["title", "is_published", "created_at"]
    list_filter = ["is_published"]
    search_fields = ["title"]


class AgentResponseInline(admin.TabularInline):
    model = AgentResponse
    extra = 0
    can_delete = False
    fields = ["side", "stance", "status", "model_name", "prompt_tokens", "completion_tokens"]
    readonly_fields = fields


@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = ["user", "scenario", "created_at", "submitted_at", "total_tokens"]
    list_filter = ["scenario"]
    search_fields = ["user__username"]
    readonly_fields = ["user", "scenario", "user_response", "submitted_at"]
    inlines = [AgentResponseInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            tokens=Sum(F("agent_responses__prompt_tokens") + F("agent_responses__completion_tokens"))
        )

    @admin.display(description="Tokens", ordering="tokens")
    def total_tokens(self, obj):
        return obj.tokens or 0
