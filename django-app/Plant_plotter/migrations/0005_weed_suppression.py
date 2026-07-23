# Generated manually for UK weed suppression data

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Plant_plotter', '0004_plant_labels'),
    ]

    operations = [
        migrations.AddField(
            model_name='plant',
            name='weed_management_notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='plant',
            name='weed_suppressors',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='plant',
            name='weeds_suppressed',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
