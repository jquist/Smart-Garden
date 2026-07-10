import json
import time
from copy import deepcopy

from django.db import models
from django.test import TestCase

from ..models import (
    Plant,
    Companion_helpslistItem,
    Plants_avoidlistItem,
)


class SolverComparisonTest(TestCase):
    """
    API-level comparison test for Quick, Medium and Slow solvers.

    This test intentionally uses a moderate frontend-style payload.
    Large stress/timing benchmarks should be kept outside normal Django tests,
    otherwise python manage.py test becomes too slow.
    """

    AUTOSORT_URL = "/api/auto-sort/"
    comparison_rows = []

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        if not cls.comparison_rows:
            return

        print("\n\nSolver comparison results")
        print("-" * 100)
        print(
            f"{'Solver':<18}"
            f"{'HTTP':<8}"
            f"{'Score':<10}"
            f"{'Placed':<10}"
            f"{'Not placed':<12}"
            f"{'Time(s)':<10}"
        )
        print("-" * 100)

        for row in cls.comparison_rows:
            print(
                f"{str(row['algorithm']):<18}"
                f"{str(row['http_status']):<8}"
                f"{str(row['score']):<10}"
                f"{str(row['placed']):<10}"
                f"{str(row['not_placed']):<12}"
                f"{row['runtime']:<10.3f}"
            )

        print("-" * 100)

    def create_plant(self, name, spacing_between_rows=15, spacing_in_rows=15):
        values = {
            "name": name,
            "plant_directly": True,
            "spacing_between_rows": spacing_between_rows,
            "spacing_in_rows": spacing_in_rows,
            "depth": 1,
            "time_to_germinate_indoors_start": None,
            "time_to_germinate_indoors_end": None,
            "time_to_germinate_indoors_period": None,
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

    def add_helps(self, plant, other):
        Companion_helpslistItem.objects.create(
            plant=plant,
            other_plant=other,
        )

    def add_avoid(self, plant, other):
        Plants_avoidlistItem.objects.create(
            plant=plant,
            other_plant=other,
        )

    def setUp(self):
        carrot = self.create_plant("carrot")
        lettuce = self.create_plant("lettuce")
        tomato = self.create_plant("tomato")
        basil = self.create_plant("basil")
        dill = self.create_plant("dill")

        self.add_helps(carrot, lettuce)
        self.add_helps(lettuce, carrot)

        self.add_helps(tomato, basil)
        self.add_helps(basil, tomato)

        self.add_avoid(carrot, dill)
        self.add_avoid(dill, carrot)

        self.base_payload = {
            "boxes": [
                {"rows": 5, "cols": 5},
                {"rows": 4, "cols": 4},
            ],
            "plants": [
                {"name": "carrot", "amount": 3},
                {"name": "lettuce", "amount": 2},
                {"name": "tomato", "amount": 2},
                {"name": "basil", "amount": 2},
                {"name": "dill", "amount": 1},
            ],
            "locked_plants": [
                {"name": "tomato", "box_index": 0, "row": 0, "col": 0},
                {"name": "carrot", "box_index": 1, "row": 1, "col": 1},
            ],
            "next_to": True,
            "avoid": True,
            "fill": False,
            "force_row": False,
            "force_column": False,
            "maximise_search": False,
            "no_companion_overlap": False,
            "cell_cm": 15,
            "time_limit": 3,
            "k": 2,
        }

    def post_autosort(self, algorithm):
        payload = deepcopy(self.base_payload)
        payload["algorithm"] = algorithm

        if algorithm == "backtracking_k":
            payload["k"] = 2

        if algorithm == "constraint":
            payload["time_limit"] = 3
            payload["maximise_search"] = False

        start = time.perf_counter()

        response = self.client.post(
            self.AUTOSORT_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )

        runtime = time.perf_counter() - start

        try:
            data = response.json()
        except Exception:
            data = {
                "error": response.content.decode(errors="replace"),
                "plant_instances": [],
                "not_placed": [],
                "total_score": None,
            }

        row = {
            "algorithm": algorithm,
            "http_status": response.status_code,
            "runtime": runtime,
            "data": data,
            "score": data.get("total_score"),
            "placed": len(data.get("plant_instances", []) or []),
            "not_placed": len(data.get("not_placed", []) or []),
        }

        self.__class__.comparison_rows.append(row)

        return row

    def assert_locked_plants_preserved(self, algorithm, data):
        instances = data.get("plant_instances", []) or []

        for locked in self.base_payload["locked_plants"]:
            found = any(
                plant.get("name") == locked["name"]
                and plant.get("box_index") == locked["box_index"]
                and plant.get("row") == locked["row"]
                and plant.get("col") == locked["col"]
                for plant in instances
            )

            self.assertTrue(
                found,
                msg=f"{algorithm} did not preserve locked plant: {locked}",
            )

    def assert_valid_solver_result(self, row):
        algorithm = row["algorithm"]
        data = row["data"]

        self.assertEqual(
            row["http_status"],
            200,
            msg=f"{algorithm} failed with response: {data}",
        )

        self.assertIn("plant_instances", data)
        self.assertIn("total_score", data)
        self.assertIn("not_placed", data)

        self.assertIsInstance(data["plant_instances"], list)
        self.assertIsInstance(data["not_placed"], list)

        requested_unlocked_total = sum(
            item["amount"]
            for item in self.base_payload["plants"]
        )
        locked_total = len(self.base_payload["locked_plants"])
        max_expected_returned = requested_unlocked_total + locked_total

        self.assertLessEqual(
            row["placed"],
            max_expected_returned,
            msg=(
                f"{algorithm} returned more plants than expected. "
                f"Placed={row['placed']}, expected max={max_expected_returned}"
            ),
        )

        self.assertGreater(
            row["placed"],
            0,
            msg=f"{algorithm} placed no plants",
        )

        self.assertIsNotNone(
            row["score"],
            msg=f"{algorithm} did not return a score",
        )

        self.assert_locked_plants_preserved(algorithm, data)

    def test_compare_quick_medium_and_slow_on_frontend_style_payload(self):
        results = [
            self.post_autosort("quick"),
            self.post_autosort("backtracking_k"),
            self.post_autosort("constraint"),
        ]

        for row in results:
            with self.subTest(algorithm=row["algorithm"]):
                self.assert_valid_solver_result(row)

        quick = next(row for row in results if row["algorithm"] == "quick")
        medium = next(row for row in results if row["algorithm"] == "backtracking_k")
        slow = next(row for row in results if row["algorithm"] == "constraint")

        # The comparison is recorded through score/time/placement values.
        # Do not force medium/slow to always beat quick, because the algorithms
        # use different search strategies and may legitimately trade score for time.
        self.assertLess(
            quick["runtime"],
            5,
            msg=f"Quick solver took too long: {quick['runtime']:.3f}s",
        )

        self.assertLess(
            medium["runtime"],
            20,
            msg=f"Medium solver took too long: {medium['runtime']:.3f}s",
        )

        self.assertLess(
            slow["runtime"],
            20,
            msg=f"Slow solver took too long: {slow['runtime']:.3f}s",
        )