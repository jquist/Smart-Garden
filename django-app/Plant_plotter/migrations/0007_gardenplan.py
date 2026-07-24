from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("Plant_plotter", "0006_refresh_seed_plant_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="GardenPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                (
                    "plan_type",
                    models.CharField(
                        choices=[("garden", "Garden planner"), ("weed", "Weed control planner")],
                        default="garden",
                        max_length=16,
                    ),
                ),
                ("boxes", models.JSONField(blank=True, default=list)),
                ("plant_instances", models.JSONField(blank=True, default=list)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="garden_plans",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at", "-created_at"],
            },
        ),
    ]
