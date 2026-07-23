from django.core.management.base import BaseCommand, CommandError
import os
from django.core.management.base import BaseCommand
from django.core.files.images import ImageFile
import json
from datetime import date
from ...models import Plant, Companion_helped_bylistItem, Companion_helpslistItem, Plants_avoidlistItem
from django.contrib.auth.models import User, Permission

ROOT_DIR = os.path.dirname(__file__)

class Command(BaseCommand):
    help = 'Insert sample data into database for tests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-if-plants-exist',
            action='store_true',
            help='Do not seed when the database already contains plants.',
        )
    
    def handle(self, *args, **options):
        if options['skip_if_plants_exist'] and Plant.objects.exists():
            print('plant seed skipped because plants already exist')
            return

        with open(ROOT_DIR + "/sample_data.json") as json_file:
            sample_data = json.load(json_file)

        Plant.objects.all().delete()
        for data in sample_data['plants'] :
            kwargs = {
                'name': data['name'],
                'plant_category': data.get('plant_category', 'vegetable'),
                'plant_roles': data.get('plant_roles', []),
                'plant_directly': data['plant_directly'],
                'spacing_between_rows': data['spacing_between_rows'],
                'spacing_in_rows': data['spacing_in_rows'],
                'depth': data['depth'],
                'time_to_germinate_indoors_start': data['time_to_germinate_indoors_start'],
                'time_to_germinate_indoors_end': data['time_to_germinate_indoors_end'],
                'time_to_germinate_indoors_period': data['time_to_germinate_indoors_period'],
                'plant_start': data['plant_start'],
                'plant_end': data['plant_end'],
                'time_first_harvets': data['time_first_harvets'],
                'harest_start': data['harest_start'],
                'harest_end': data['harest_end'],
                
    
            }
            '''
            image_path = album['cover']
            if image_path is not None:
                kwargs['cover_image'] = ImageFile(open(ROOT_DIR +"/" +image_path, 'rb'),
                                            name=image_path)
                    
                    'companion_helps': Plant['companion_helps'],
                    'companion_helped_by': Plant['companion_helped_by'],
                    'plants_avoid': Plant['plants_avoid'],
            
            
            '''
         
            Plant(**kwargs).save()
        print('plant seed made')

        for i in sample_data['plants']:
            plant_obj = Plant.objects.get(name=i['name'])
            for other_name in i.get('companion_helps', []):
                other_obj = Plant.objects.get(name=other_name)
                Companion_helpslistItem.objects.get_or_create(plant=plant_obj,other_plant=other_obj)
        print('compaion helps seed made')


        for i in sample_data['plants']:
            plant_obj = Plant.objects.get(name=i['name'])
            for other_name in i.get('companion_helped_by', []):
                other_obj = Plant.objects.get(name=other_name)
                Companion_helped_bylistItem.objects.get_or_create(plant=plant_obj,other_plant=other_obj)

        print('compaion helps by seed made')


        '''
        for i in sample_data['plants']:
                    for data in i['plants_avoid']:
                        kwargs = {
                            'plant' : Plant.objects.get(name=i['name']),
                            'other_plant' : Plant.objects.get(name=data)
                        }
                    Plants_avoidlistItem(**kwargs).save()
        '''
        for i in sample_data['plants']:
            plant_obj = Plant.objects.get(name=i['name'])
            for other_name in i.get('plants_avoid', []):
                other_obj = Plant.objects.get(name=other_name)
                Plants_avoidlistItem.objects.get_or_create(plant=plant_obj,other_plant=other_obj)

        print('avoid seed made')
        
