from django.db import migrations

DOMAINS = ["dsu.edu", "trojans.dsu.edu"]


def add_domains(apps, schema_editor):
    AllowedDomain = apps.get_model("accounts", "AllowedDomain")
    for domain in DOMAINS:
        AllowedDomain.objects.get_or_create(domain=domain)


def remove_domains(apps, schema_editor):
    apps.get_model("accounts", "AllowedDomain").objects.filter(domain__in=DOMAINS).delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [migrations.RunPython(add_domains, remove_domains)]
