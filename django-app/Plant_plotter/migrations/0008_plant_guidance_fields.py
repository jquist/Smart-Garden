from django.db import migrations, models


def fill_plant_guidance(apps, schema_editor):
    Plant = apps.get_model("Plant_plotter", "Plant")

    def clean(value):
        if value in (None, "", "null"):
            return ""
        return str(value).strip()

    category_labels = {
        "cover_crop": "cover crop",
        "flower": "flower",
        "fruit": "fruiting plant",
        "herb": "herb",
        "ornamental": "ornamental plant",
        "tree_shrub": "tree or shrub",
        "vegetable": "vegetable",
        "weed": "weed or problem plant",
        "wildlife_native": "wildlife-friendly native plant",
    }
    role_labels = {
        "aromatic_pest_confuser": "aromatic companion planting",
        "beneficial_insect_plant": "beneficial insects",
        "cover_crop": "soil cover",
        "edible": "edible harvests",
        "flowering": "flowers",
        "green_manure": "green manure",
        "ground_cover": "ground cover",
        "living_mulch": "living mulch",
        "nitrogen_fixer": "nitrogen fixing",
        "ornamental": "ornamental value",
        "perennial_plant": "perennial growth",
        "pollinator": "pollinators",
        "soil_improver": "soil improvement",
        "toxic": "careful handling",
        "weed": "weed monitoring",
        "weed_suppressor": "weed suppression",
        "wildlife_support": "wildlife support",
    }

    def role_text(roles):
        labels = [role_labels.get(role, str(role).replace("_", " ")) for role in roles or []]
        if not labels:
            return ""
        if len(labels) == 1:
            return labels[0]
        return ", ".join(labels[:-1]) + f" and {labels[-1]}"

    def description_for(plant):
        category = category_labels.get(plant.plant_category, "garden plant")
        roles = role_text(plant.plant_roles)
        if plant.plant_category == "weed":
            text = f"{plant.name} is a {category} to watch for when planning beds."
            if plant.weed_management_notes:
                text += f" {plant.weed_management_notes}"
            return text

        text = f"{plant.name} is a {category}"
        if roles:
            text += f" valued for {roles}"
        text += "."
        if plant.weeds_suppressed:
            text += f" It can be useful in weed-control plans for suppressing {', '.join(plant.weeds_suppressed[:3])}."
        return text

    def tips_for(plant):
        tips = []
        if plant.plant_category == "weed":
            tips.append("Map where it appears before choosing suppressor plants or removal work.")
        elif plant.plant_directly:
            tips.append("Best suited to direct sowing in its final growing position.")
        else:
            tips.append("Can be started in modules or pots before moving into the bed.")

        row_spacing = int(plant.spacing_between_rows or 0)
        plant_spacing = int(plant.spacing_in_rows or 0)
        if row_spacing or plant_spacing:
            tips.append(f"Aim for about {row_spacing} cm between rows and {plant_spacing} cm between plants.")

        depth = int(plant.depth or 0)
        if depth:
            tips.append(f"Sow around {depth} cm deep, then firm the soil gently.")

        start = clean(plant.plant_start)
        end = clean(plant.plant_end)
        if start and end:
            tips.append(f"Typical outdoor planting window: {start} to {end}.")

        harvest_start = clean(plant.harest_start)
        harvest_end = clean(plant.harest_end)
        if harvest_start and harvest_end and plant.plant_category != "weed":
            tips.append(f"Plan harvest checks from {harvest_start} to {harvest_end}.")

        return " ".join(tips)

    def how_to_for(plant):
        if plant.plant_category == "weed":
            return (
                "Identify the patch, estimate how much space it covers, and avoid letting it set seed. "
                "Remove what you can by hand or hoeing, then use suitable ground-cover or suppressor plants "
                "to reduce open soil where it can return."
            )

        steps = [
            "Prepare a weed-free bed with loose, moist soil.",
            "Mark rows or planting spots using the spacing shown on this profile.",
        ]
        if plant.plant_directly:
            steps.append("Sow seed evenly at the recommended depth and water with a gentle spray.")
        else:
            steps.append("Raise young plants in modules or pots, then transplant once roots hold together.")
        steps.extend([
            "Keep the area watered while plants establish.",
            "Thin or re-space crowded seedlings so each plant has room to grow.",
            "Check regularly for weeds, pests, and harvest readiness.",
        ])
        return " ".join(steps)

    plants_to_update = []
    for plant in Plant.objects.all():
        if not plant.description:
            plant.description = description_for(plant)
        if not plant.planting_tips:
            plant.planting_tips = tips_for(plant)
        if not plant.planting_how_to:
            plant.planting_how_to = how_to_for(plant)
        plants_to_update.append(plant)

    if plants_to_update:
        Plant.objects.bulk_update(
            plants_to_update,
            ["description", "planting_tips", "planting_how_to"],
            batch_size=500,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("Plant_plotter", "0007_gardenplan"),
    ]

    operations = [
        migrations.AddField(
            model_name="plant",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="plant",
            name="planting_tips",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="plant",
            name="planting_how_to",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RunPython(fill_plant_guidance, migrations.RunPython.noop),
    ]
