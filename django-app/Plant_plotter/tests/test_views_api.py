import json

from django.db import models
from django.test import TestCase

from ..models import (
    Plant,
    Companion_helpslistItem,
    Companion_helped_bylistItem,
    Plants_avoidlistItem,
)


class ViewsAPITest(TestCase):
    HOME_URL = "/"
    PLANT_URL = "/api/plant/"
    HELP_URL = "/api/help/"
    HELP_BY_URL = "/api/help_by/"
    AVOID_URL = "/api/avoid/"
    AUTOSORT_URL = "/api/auto-sort/"

    def create_plant(self, name, spacing_between_rows=15, spacing_in_rows=15):
        values = {
            "name": name,
            "plant_directly": True,
            "spacing_between_rows": spacing_between_rows,
            "spacing_in_rows": spacing_in_rows,
            "depth": 1,
            "plant_start": "march",
            "plant_end": "june",
            "time_first_harvets": 2,
            "time_first_harvest": 2,
            "harest_start": "july",
            "harest_end": "september",
            "harvest_start": "july",
            "harvest_end": "september",
        }

        kwargs = {}

        for field in Plant._meta.fields:
            if field.primary_key:
                continue

            if field.name in values:
                kwargs[field.name] = values[field.name]
                continue

            if field.has_default() or field.null:
                continue

            if isinstance(field, models.BooleanField):
                kwargs[field.name] = False
            elif isinstance(field, models.IntegerField):
                kwargs[field.name] = 1
            elif isinstance(field, models.FloatField):
                kwargs[field.name] = 1.0
            elif isinstance(field, models.CharField):
                kwargs[field.name] = ""
            elif isinstance(field, models.TextField):
                kwargs[field.name] = ""

        return Plant.objects.create(**kwargs)

    def setUp(self):
        self.carrot = self.create_plant("carrot")
        self.lettuce = self.create_plant("lettuce")
        self.dill = self.create_plant("dill")

        Companion_helpslistItem.objects.create(
            plant=self.carrot,
            other_plant=self.lettuce,
        )

        Companion_helped_bylistItem.objects.create(
            plant=self.carrot,
            other_plant=self.lettuce,
        )

        Plants_avoidlistItem.objects.create(
            plant=self.carrot,
            other_plant=self.dill,
        )

    def as_list(self, data):
        if isinstance(data, list):
            return data
        return data.get("results", [])

    def test_homepage_loads(self):
        response = self.client.get(self.HOME_URL)
        self.assertEqual(response.status_code, 200)

    def test_plant_endpoint_returns_database_plants(self):
        response = self.client.get(self.PLANT_URL)

        self.assertEqual(response.status_code, 200)

        data = self.as_list(response.json())
        names = {item.get("name") for item in data}

        self.assertIn("carrot", names)
        self.assertIn("lettuce", names)
        self.assertIn("dill", names)

    def test_help_endpoint_returns_companion_helps_relationships(self):
        response = self.client.get(self.HELP_URL, {"plant": self.carrot.id})

        self.assertEqual(response.status_code, 200)

        data = self.as_list(response.json())

        self.assertTrue(
            any(item.get("other_plant_name") == "lettuce" for item in data),
            msg=f"Expected carrot to help lettuce, got: {data}",
        )

    def test_help_by_endpoint_returns_companion_helped_by_relationships(self):
        response = self.client.get(self.HELP_BY_URL, {"plant": self.carrot.id})

        self.assertEqual(response.status_code, 200)

        data = self.as_list(response.json())

        self.assertTrue(
            any(item.get("other_plant_name") == "lettuce" for item in data),
            msg=f"Expected carrot to be helped by lettuce, got: {data}",
        )

    def test_avoid_endpoint_returns_avoid_relationships(self):
        response = self.client.get(self.AVOID_URL, {"plant": self.carrot.id})

        self.assertEqual(response.status_code, 200)

        data = self.as_list(response.json())

        self.assertTrue(
            any(item.get("other_plant_name") == "dill" for item in data),
            msg=f"Expected carrot to avoid dill, got: {data}",
        )

    def test_autosort_endpoint_accepts_frontend_style_payload(self):
        payload = {
            "algorithm": "quick",
            "boxes": [{"rows": 4, "cols": 4}],
            "plants": [
                {"name": "carrot", "amount": 1},
                {"name": "lettuce", "amount": 1},
            ],
            "locked_plants": [],
            "next_to": True,
            "avoid": True,
            "fill": False,
            "force_row": False,
            "force_column": False,
            "maximise_search": False,
            "no_companion_overlap": False,
            "cell_cm": 15,
            "time_limit": 5,
            "k": 3,
        }

        response = self.client.post(
            self.AUTOSORT_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
            msg=response.content.decode(),
        )

        data = response.json()

        self.assertIn("plant_instances", data)
        self.assertIn("not_placed", data)
        self.assertIn("total_score", data)

        self.assertIsInstance(data["plant_instances"], list)
        self.assertIsInstance(data["not_placed"], list)

        self.assertGreater(
            len(data["plant_instances"]),
            0,
            msg="Autosort API returned no placed plants for a simple valid payload.",
        )

    def test_autosort_endpoint_rejects_unknown_algorithm(self):
        payload = {
            "algorithm": "not_a_real_solver",
            "boxes": [{"rows": 4, "cols": 4}],
            "plants": [{"name": "carrot", "amount": 1}],
            "locked_plants": [],
            "cell_cm": 15,
        }

        response = self.client.post(
            self.AUTOSORT_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
            msg=response.content.decode(),
        )