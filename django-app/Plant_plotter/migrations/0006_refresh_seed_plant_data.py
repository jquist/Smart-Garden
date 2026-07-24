# Data refresh was moved to the Render startup seed command so migrations can
# finish quickly and the web service can bind to its port in time.

from django.db import migrations


def refresh_seed_data(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("Plant_plotter", "0005_weed_suppression"),
    ]

    operations = [
        migrations.RunPython(refresh_seed_data, migrations.RunPython.noop),
    ]
