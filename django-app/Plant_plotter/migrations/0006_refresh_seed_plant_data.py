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
    helps_model = apps.get_model("Plant_plotter", "Companion_helpslistItem")
    helped_by_model = apps.get_model(
        "Plant_plotter",
        "Companion_helped_bylistItem",
    )
    avoid_model = apps.get_model("Plant_plotter", "Plants_avoidlistItem")

    sample_path = (
        Path(__file__).resolve().parents[1]
        / "management"
        / "commands"
        / "sample_data.json"
    )
    sample_plants = json.loads(sample_path.read_text(encoding="utf-8"))["plants"]

    plants_by_name = {}
    for data in sample_plants:
        defaults = {
            field: data.get(field, default)
            for field, default in PLANT_FIELD_DEFAULTS.items()
        }
        plant, _ = plant_model.objects.update_or_create(
            name=data["name"],
            defaults=defaults,
        )
        plants_by_name[plant.name] = plant

    seed_ids = [plant.id for plant in plants_by_name.values()]
    helps_model.objects.filter(plant_id__in=seed_ids).delete()
    helped_by_model.objects.filter(plant_id__in=seed_ids).delete()
    avoid_model.objects.filter(plant_id__in=seed_ids).delete()

    for data in sample_plants:
        plant = plants_by_name[data["name"]]
        for other_name in data.get("companion_helps", []):
            helps_model.objects.get_or_create(
                plant=plant,
                other_plant=plants_by_name[other_name],
            )
        for other_name in data.get("companion_helped_by", []):
            helped_by_model.objects.get_or_create(
                plant=plant,
                other_plant=plants_by_name[other_name],
            )
        for other_name in data.get("plants_avoid", []):
            avoid_model.objects.get_or_create(
                plant=plant,
                other_plant=plants_by_name[other_name],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("Plant_plotter", "0005_weed_suppression"),
    ]

    operations = [
        migrations.RunPython(refresh_seed_data, migrations.RunPython.noop),
    ]
