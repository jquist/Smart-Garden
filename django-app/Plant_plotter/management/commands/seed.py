import json
import os
from collections import Counter

from django.core.management.base import BaseCommand

from ...models import (
    Companion_helped_bylistItem,
    Companion_helpslistItem,
    Plant,
    Plants_avoidlistItem,
)


ROOT_DIR = os.path.dirname(__file__)
PLANT_FIELDS = [
    "plant_category",
    "plant_roles",
    "weed_suppressors",
    "weeds_suppressed",
    "weed_management_notes",
    "plant_directly",
    "spacing_between_rows",
    "spacing_in_rows",
    "depth",
    "time_to_germinate_indoors_start",
    "time_to_germinate_indoors_end",
    "time_to_germinate_indoors_period",
    "plant_start",
    "plant_end",
    "time_first_harvets",
    "harest_start",
    "harest_end",
]


def plant_kwargs(data):
    return {
        "name": data["name"],
        "plant_category": data.get("plant_category", "vegetable"),
        "plant_roles": data.get("plant_roles", []),
        "weed_suppressors": data.get("weed_suppressors", []),
        "weeds_suppressed": data.get("weeds_suppressed", []),
        "weed_management_notes": data.get("weed_management_notes", ""),
        "plant_directly": data["plant_directly"],
        "spacing_between_rows": data["spacing_between_rows"],
        "spacing_in_rows": data["spacing_in_rows"],
        "depth": data["depth"],
        "time_to_germinate_indoors_start": data[
            "time_to_germinate_indoors_start"
        ],
        "time_to_germinate_indoors_end": data["time_to_germinate_indoors_end"],
        "time_to_germinate_indoors_period": data[
            "time_to_germinate_indoors_period"
        ],
        "plant_start": data["plant_start"],
        "plant_end": data["plant_end"],
        "time_first_harvets": data["time_first_harvets"],
        "harest_start": data["harest_start"],
        "harest_end": data["harest_end"],
    }


class Command(BaseCommand):
    help = "Insert or refresh sample plant data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-if-plants-exist",
            action="store_true",
            help="Do not seed when the database already contains plants.",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help=(
                "Update seed plants and create missing seed plants without deleting "
                "custom plants."
            ),
        )

    def handle(self, *args, **options):
        if (
            options["skip_if_plants_exist"]
            and Plant.objects.exists()
            and not options["update_existing"]
        ):
            print("plant seed skipped because plants already exist")
            return

        with open(os.path.join(ROOT_DIR, "sample_data.json"), encoding="utf-8") as json_file:
            sample_data = json.load(json_file)

        sample_plants = sample_data["plants"]

        if not options["update_existing"]:
            Plant.objects.all().delete()

        sample_names = [data["name"] for data in sample_plants]
        existing_plants = Plant.objects.in_bulk(sample_names, field_name="name")
        plants_to_create = []
        plants_to_update = []

        for data in sample_plants:
            kwargs = plant_kwargs(data)

            if options["update_existing"]:
                name = kwargs.pop("name")
                plant = existing_plants.get(name)
                if plant:
                    for field, value in kwargs.items():
                        setattr(plant, field, value)
                    plants_to_update.append(plant)
                else:
                    plants_to_create.append(Plant(name=name, **kwargs))
            else:
                plants_to_create.append(Plant(**kwargs))

        if plants_to_create:
            Plant.objects.bulk_create(plants_to_create, batch_size=500)
        if plants_to_update:
            Plant.objects.bulk_update(
                plants_to_update,
                PLANT_FIELDS,
                batch_size=500,
            )

        plants_by_name = Plant.objects.in_bulk(sample_names, field_name="name")
        created_count = len(plants_to_create)
        updated_count = len(plants_to_update)

        if options["update_existing"]:
            seed_ids = [plant.id for plant in plants_by_name.values()]
            Companion_helpslistItem.objects.filter(plant_id__in=seed_ids).delete()
            Companion_helped_bylistItem.objects.filter(plant_id__in=seed_ids).delete()
            Plants_avoidlistItem.objects.filter(plant_id__in=seed_ids).delete()

        print(
            f"plant seed made: {created_count} created, {updated_count} updated"
        )

        help_items = []
        for data in sample_plants:
            plant_obj = plants_by_name[data["name"]]
            for other_name in data.get("companion_helps", []):
                other_obj = plants_by_name[other_name]
                help_items.append(
                    Companion_helpslistItem(
                        plant=plant_obj,
                        other_plant=other_obj,
                    )
                )
        Companion_helpslistItem.objects.bulk_create(
            help_items,
            batch_size=1000,
            ignore_conflicts=True,
        )
        print("companion helps seed made")

        helped_by_items = []
        for data in sample_plants:
            plant_obj = plants_by_name[data["name"]]
            for other_name in data.get("companion_helped_by", []):
                other_obj = plants_by_name[other_name]
                helped_by_items.append(
                    Companion_helped_bylistItem(
                        plant=plant_obj,
                        other_plant=other_obj,
                    )
                )
        Companion_helped_bylistItem.objects.bulk_create(
            helped_by_items,
            batch_size=1000,
            ignore_conflicts=True,
        )
        print("companion helped by seed made")

        avoid_items = []
        for data in sample_plants:
            plant_obj = plants_by_name[data["name"]]
            for other_name in data.get("plants_avoid", []):
                other_obj = plants_by_name[other_name]
                avoid_items.append(
                    Plants_avoidlistItem(
                        plant=plant_obj,
                        other_plant=other_obj,
                    )
                )
        Plants_avoidlistItem.objects.bulk_create(
            avoid_items,
            batch_size=1000,
            ignore_conflicts=True,
        )
        print("avoid seed made")

        category_counts = Counter(
            Plant.objects.values_list("plant_category", flat=True)
        )
        weed_count = category_counts.get("weed", 0)
        print(f"plant categories: {dict(sorted(category_counts.items()))}")
        print(f"weed plants in database: {weed_count}")
