import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile
import json
from datetime import date
from ...models import Plant, Companion_helpslistItem, Companion_helped_bylistItem, Plants_avoidlistItem
from django.contrib.auth.models import User, Permission
from pathlib import Path

ROOT_DIR = os.path.dirname(__file__)


class Command(BaseCommand):
    help = 'Initial boostrapper for Plant_plotter_settings deployments'

    def handle(self, *args, **options):
        Plant.objects.all().delete()
        User.objects.all().delete()

        with open(ROOT_DIR + "/sample_data.json") as json_file:
            sample_data = json.load(json_file)

        j=1
        for plant in sample_data['plants']:
            kwargs = { 
                "id": j,
                "name":plant['name'],
                "plant_category":plant.get("plant_category", "vegetable"),
                "plant_roles":plant.get("plant_roles", []),
                "weed_suppressors":plant.get("weed_suppressors", []),
                "weeds_suppressed":plant.get("weeds_suppressed", []),
                "weed_management_notes":plant.get("weed_management_notes", ""),
                "plant_directly":plant["plant_directly"],
                "spacing_between_rows":plant["spacing_between_rows"],
                "spacing_in_rows":plant["spacing_in_rows"],
                "depth":plant["depth"],
                "time_to_germinate_indoors_start":plant["time_to_germinate_indoors_start"],
                "time_to_germinate_indoors_end":plant["time_to_germinate_indoors_end"],
                "time_to_germinate_indoors_period":plant["time_to_germinate_indoors_period"],
                "plant_start":plant["plant_start"],
                "plant_end" :plant["plant_end"],
                "time_first_harvets" :plant["time_first_harvets"],
                "harest_start":plant["harest_start"],
                "harest_end":plant["harest_end"],
            }
            Plant(**kwargs).save()
            j+=1

        for plant in sample_data['plants']:
            plant_obj = Plant.objects.get(name=plant['name'])
            for other_name in plant.get('companion_helps', []):
                other_obj = Plant.objects.get(name=other_name)
                Companion_helpslistItem.objects.get_or_create(
                    plant=plant_obj,
                    other_plant=other_obj,
                )
            for other_name in plant.get('companion_helped_by', []):
                other_obj = Plant.objects.get(name=other_name)
                Companion_helped_bylistItem.objects.get_or_create(
                    plant=plant_obj,
                    other_plant=other_obj,
                )
            for other_name in plant.get('plants_avoid', []):
                other_obj = Plant.objects.get(name=other_name)
                Plants_avoidlistItem.objects.get_or_create(
                    plant=plant_obj,
                    other_plant=other_obj,
                )

        print('Seeding done.')

