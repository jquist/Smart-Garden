import json
from collections import defaultdict
from copy import deepcopy

from django.db import models
from django.test import TestCase

from ..models import (
    Plant,
    Companion_helpslistItem,
    Plants_avoidlistItem,
)


class SolverRulesTest(TestCase):
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

    def add_helps(self, plant, other):
        Companion_helpslistItem.objects.create(plant=plant, other_plant=other)

    def add_avoid(self, plant, other):
        Plants_avoidlistItem.objects.create(plant=plant, other_plant=other)

    def setUp(self):
        self.carrot = self.create_plant("carrot")
        self.lettuce = self.create_plant("lettuce")
        self.dill = self.create_plant("dill")
        self.tomato = self.create_plant("tomato")
        self.basil = self.create_plant("basil")

        self.add_helps(self.carrot, self.lettuce)
        self.add_helps(self.lettuce, self.carrot)

        self.add_helps(self.tomato, self.basil)
        self.add_helps(self.basil, self.tomato)

        self.add_avoid(self.carrot, self.dill)
        self.add_avoid(self.dill, self.carrot)

    def post_autosort(self, payload):
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

        return response.json()

    def occupied_cells(self, plant_instances):
        cells = defaultdict(list)

        for plant in plant_instances:
            name = plant["name"]
            box_index = plant["box_index"]
            row = plant["row"]
            col = plant["col"]
            height = plant.get("height", 1)
            width = plant.get("width", 1)

            for r in range(row, row + height):
                for c in range(col, col + width):
                    cells[(box_index, r, c)].append(name)

        return cells

    def assert_no_pair_overlap(self, data, plant_a, plant_b):
        cells = self.occupied_cells(data.get("plant_instances", []))

        for cell, names in cells.items():
            self.assertFalse(
                plant_a in names and plant_b in names,
                msg=f"{plant_a} and {plant_b} illegally overlap in cell {cell}: {names}",
            )

    def assert_no_different_type_overlap(self, data):
        cells = self.occupied_cells(data.get("plant_instances", []))

        for cell, names in cells.items():
            unique_names = set(names)

            self.assertLessEqual(
                len(unique_names),
                1,
                msg=f"Different plant types overlap in cell {cell}: {names}",
            )

    def solver_payload(self, algorithm, extra=None):
        payload = {
            "algorithm": algorithm,
            "boxes": [{"rows": 3, "cols": 3}],
            "plants": [],
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

        if extra:
            payload.update(deepcopy(extra))

        return payload

    def test_avoid_plants_do_not_overlap_for_all_solvers(self):
        algorithms = ["quick", "backtracking_k", "constraint"]

        for algorithm in algorithms:
            with self.subTest(algorithm=algorithm):
                payload = self.solver_payload(
                    algorithm,
                    {
                        "boxes": [{"rows": 2, "cols": 2}],
                        "plants": [
                            {"name": "carrot", "amount": 1},
                            {"name": "dill", "amount": 1},
                        ],
                        "avoid": True,
                    },
                )

                data = self.post_autosort(payload)
                self.assert_no_pair_overlap(data, "carrot", "dill")

    def test_no_companion_overlap_blocks_different_type_overlap_for_all_solvers(self):
        algorithms = ["quick", "backtracking_k", "constraint"]

        for algorithm in algorithms:
            with self.subTest(algorithm=algorithm):
                payload = self.solver_payload(
                    algorithm,
                    {
                        "boxes": [{"rows": 1, "cols": 1}],
                        "plants": [
                            {"name": "carrot", "amount": 1},
                            {"name": "lettuce", "amount": 1},
                        ],
                        "avoid": True,
                        "no_companion_overlap": True,
                    },
                )

                data = self.post_autosort(payload)
                self.assert_no_different_type_overlap(data)

                self.assertLessEqual(
                    len(data.get("plant_instances", [])),
                    1,
                    msg=(
                        f"{algorithm} placed more than one plant in a one-cell box "
                        "despite no_companion_overlap=True"
                    ),
                )

    def test_locked_plant_position_is_preserved_for_all_solvers(self):
        algorithms = ["quick", "backtracking_k", "constraint"]

        for algorithm in algorithms:
            with self.subTest(algorithm=algorithm):
                payload = self.solver_payload(
                    algorithm,
                    {
                        "boxes": [{"rows": 4, "cols": 4}],
                        "plants": [
                            {"name": "tomato", "amount": 1},
                            {"name": "basil", "amount": 2},
                        ],
                        "locked_plants": [
                            {"name": "tomato", "box_index": 0, "row": 1, "col": 1},
                        ],
                    },
                )

                data = self.post_autosort(payload)

                locked_tomato_found = any(
                    plant.get("name") == "tomato"
                    and plant.get("box_index") == 0
                    and plant.get("row") == 1
                    and plant.get("col") == 1
                    for plant in data.get("plant_instances", [])
                )

                self.assertTrue(
                    locked_tomato_found,
                    msg=f"{algorithm} did not preserve the locked tomato placement",
                )

    def test_solver_response_contains_required_fields_for_rule_tests(self):
        payload = self.solver_payload(
            "quick",
            {
                "plants": [
                    {"name": "carrot", "amount": 1},
                    {"name": "lettuce", "amount": 1},
                ],
            },
        )

        data = self.post_autosort(payload)

        self.assertIn("plant_instances", data)
        self.assertIn("not_placed", data)
        self.assertIn("total_score", data)
        self.assertIsInstance(data["plant_instances"], list)
        self.assertIsInstance(data["not_placed"], list)