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
        a=1
        b=1
        c=1
        for plant in sample_data['plants']:
            kwargs = { 
                "id": j,
                "name":plant['name'],
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
            i = 0
            for companion_helps in plant['companion_helps']:
                Companion_helpslistItem(id=a,plant=Plant.objects.get(name=companion_helps),
                            plant=Plant.objects.get(name=plant['name']),position = i).save()
                i = i + 1
                a +=1
            t = 0
            for companion_helped_by in plant['companion_helped_by']:
                Companion_helped_bylistItem(id=b,plant=Plant.objects.get(name=companion_helped_by),
                            plant=Plant.objects.get(name=plant['name']),position = t).save()
                t = t + 1
                b +=1

            k = 0
            for plants_avoid in plant['plants_avoid']:
                Plants_avoidlistItem(id=c,plant=Plant.objects.get(name=plants_avoid),
                            plant=Plant.objects.get(name=plant['name']),position = k).save()
                k = k + 1
                c +=1
                
            j+=1

        print('Seeding done.')

