from django.urls import path

from . import views

app_name = "sims"

urlpatterns = [
    path("", views.scenario_list, name="scenario_list"),
    path("scenarios/<int:scenario_id>/start/", views.start, name="start"),
    path("sim/<int:sim_id>/", views.simulation, name="simulation"),
    path("sim/<int:sim_id>/submit/", views.submit, name="submit"),
    path("sim/<int:sim_id>/status/", views.status, name="status"),
]
