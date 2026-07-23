# Generated manually for plant data labelling

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Plant_plotter', '0003_alter_companion_helped_bylistitem_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='plant',
            name='plant_category',
            field=models.CharField(default='vegetable', max_length=64),
        ),
        migrations.AddField(
            model_name='plant',
            name='plant_roles',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
