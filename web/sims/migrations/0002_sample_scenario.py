from django.db import migrations

TITLE = "Sample: Baltic exercise buildup"


def add_sample(apps, schema_editor):
    Scenario = apps.get_model("sims", "Scenario")
    Scenario.objects.get_or_create(
        title=TITLE,
        defaults={
            "background": (
                "Placeholder scenario for development. Replace it with the Policy Lab's real scenarios.\n\n"
                "The adversary state has announced large-scale military exercises near the border of a Baltic "
                "NATO member, moving an estimated 40,000 troops to within 50 km of the border. Allied "
                "intelligence cannot rule out that the exercise is cover for a limited incursion. The Baltic "
                "government has requested consultations under Article 4."
            ),
            "prompt": "How should your side respond over the next 72 hours?",
        },
    )


def remove_sample(apps, schema_editor):
    apps.get_model("sims", "Scenario").objects.filter(title=TITLE).delete()


class Migration(migrations.Migration):
    dependencies = [("sims", "0001_initial")]
    operations = [migrations.RunPython(add_sample, remove_sample)]
