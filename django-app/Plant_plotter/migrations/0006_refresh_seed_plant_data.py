# Generated manually to refresh hosted seed data after plant labelling changes.

import json
from pathlib import Path

from django.db import migrations


PLANT_FIELD_DEFAULTS = {
    "plant_category": "vegetable",
    "plant_roles": [],
    "weed_suppressors": [],
    "weeds_suppressed": [],
    "weed_management_notes": "",
    "plant_directly": False,
    "spacing_between_rows": 30,
    "spacing_in_rows": 30,
    "depth": 0,
    "time_to_germinate_indoors_start": None,
    "time_to_germinate_indoors_end": None,
    "time_to_germinate_indoors_period": 0,
    "plant_start": None,
    "plant_end": None,
    "time_first_harvets": 0,
    "harest_start": None,
    "harest_end": None,
}


def refresh_seed_data(apps, schema_editor):
    plant_model = apps.get_model("Plant_plotter", "Plant")

    sample_path = (
        Path(__file__).resolve().parents[1]
        / "management"
        / "commands"
        / "sample_data.json"
    )
    sample_plants = json.loads(sample_path.read_text(encoding="utf-8"))["plants"]

    for data in sample_plants:
        defaults = {
            field: data.get(field, default)
            for field, default in PLANT_FIELD_DEFAULTS.items()
        }
        plant_model.objects.update_or_create(
            name=data["name"],
            defaults=defaults,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("Plant_plotter", "0005_weed_suppression"),
    ]

    operations = [
        migrations.RunPython(refresh_seed_data, migrations.RunPython.noop),
    ]
