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


class SolverStressTest(TestCase):
    """
    Manual frontend-like adaptive stress benchmark.

    This file is intentionally named stress.py, not test_solver_stress.py,
    so it does not run with the normal Django test suite.

    Run manually with:

        python manage.py test Plant_plotter.tests.stress -v 2

    This benchmark tries to mimic realistic frontend autosort calls while
    increasing garden size and plant count until each solver reaches a
    practical limit.
    """

    AUTOSORT_URL = "/api/auto-sort/"
    benchmark_rows = []

    START_BOX_SIZE = 6
    START_TOTAL_PLANTS = 6
    PLANT_INCREASE_PER_LEVEL = 1
    ADD_TYPE_EVERY_N_LEVELS = 6

    # Frontend-style options.
    FRONTEND_TIME_LIMIT = 12
    CELL_CM = 15

    # Set to True if want to stress the "Force same plants together" toggle.
    FORCE_SAME_TOGETHER = True

    # Keep fill/max-spread off because it asks to compare quick, medium and constraint,
    # not quick_fill/backtracking_minmax/constraint_fill.
    FILL = False

    PLANT_TYPES = [
        "carrot",
        "lettuce",
        "tomato",
        "basil",
        "onion",
        "dill",
        "garlic",
        "spinach",
        "pepper",
        "cucumber",
        "radish",
        "cabbage",
    ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        if not cls.benchmark_rows:
            return

        print("\n\nFrontend-like adaptive solver stress benchmark results")
        print("-" * 155)
        print(
            f"{'Solver':<18}"
            f"{'Level':<8}"
            f"{'Box':<8}"
            f"{'Types':<8}"
            f"{'Req':<8}"
            f"{'Locked':<8}"
            f"{'HTTP':<8}"
            f"{'Score':<10}"
            f"{'Placed':<10}"
            f"{'Not placed':<12}"
            f"{'Time(s)':<10}"
            f"{'Note':<18}"
        )
        print("-" * 155)

        for row in cls.benchmark_rows:
            print(
                f"{str(row['solver']):<18}"
                f"{str(row['level']):<8}"
                f"{str(row['box_size']) + 'x' + str(row['box_size']):<8}"
                f"{str(row['type_count']):<8}"
                f"{str(row['requested_total']):<8}"
                f"{str(row['locked_total']):<8}"
                f"{str(row['http_status']):<8}"
                f"{str(row['score']):<10}"
                f"{str(row['placed']):<10}"
                f"{str(row['not_placed']):<12}"
                f"{row['runtime']:<10.3f}"
                f"{str(row['note']):<18}"
            )

        print("-" * 155)

    def create_plant(self, name, spacing_between_rows=30, spacing_in_rows=15):
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
        plants = {
            "carrot": self.create_plant("carrot", 30, 15),
            "lettuce": self.create_plant("lettuce", 30, 15),
            "tomato": self.create_plant("tomato", 30, 15),
            "basil": self.create_plant("basil", 15, 15),
            "onion": self.create_plant("onion", 30, 15),
            "dill": self.create_plant("dill", 30, 15),
            "garlic": self.create_plant("garlic", 30, 15),
            "spinach": self.create_plant("spinach", 30, 15),
            "pepper": self.create_plant("pepper", 30, 15),
            "cucumber": self.create_plant("cucumber", 30, 15),
            "radish": self.create_plant("radish", 15, 15),
            "cabbage": self.create_plant("cabbage", 30, 15),
        }

        # Companion relationships.
        self.add_helps(plants["carrot"], plants["lettuce"])
        self.add_helps(plants["lettuce"], plants["carrot"])

        self.add_helps(plants["tomato"], plants["basil"])
        self.add_helps(plants["basil"], plants["tomato"])

        self.add_helps(plants["carrot"], plants["onion"])
        self.add_helps(plants["onion"], plants["carrot"])

        self.add_helps(plants["garlic"], plants["lettuce"])
        self.add_helps(plants["lettuce"], plants["garlic"])

        self.add_helps(plants["spinach"], plants["lettuce"])
        self.add_helps(plants["lettuce"], plants["spinach"])

        self.add_helps(plants["pepper"], plants["basil"])
        self.add_helps(plants["basil"], plants["pepper"])

        self.add_helps(plants["cucumber"], plants["garlic"])
        self.add_helps(plants["garlic"], plants["cucumber"])

        # Avoid relationships.
        self.add_avoid(plants["carrot"], plants["dill"])
        self.add_avoid(plants["dill"], plants["carrot"])

        self.add_avoid(plants["onion"], plants["basil"])
        self.add_avoid(plants["basil"], plants["onion"])

        self.add_avoid(plants["tomato"], plants["cucumber"])
        self.add_avoid(plants["cucumber"], plants["tomato"])

        self.add_avoid(plants["cabbage"], plants["tomato"])
        self.add_avoid(plants["tomato"], plants["cabbage"])

    def build_dynamic_plants(self, level_number):
        type_count = min(
            len(self.PLANT_TYPES),
            4 + ((level_number - 1) // self.ADD_TYPE_EVERY_N_LEVELS),
        )

        active_types = self.PLANT_TYPES[:type_count]

        requested_total = (
            self.START_TOTAL_PLANTS
            + ((level_number - 1) * self.PLANT_INCREASE_PER_LEVEL)
        )

        counts = {name: 1 for name in active_types}
        remaining = max(0, requested_total - len(active_types))

        index = 0
        while remaining > 0:
            name = active_types[index % len(active_types)]
            counts[name] += 1
            remaining -= 1
            index += 1

        return [
            {"name": name, "amount": amount}
            for name, amount in counts.items()
        ]

    def build_locked_plants(self, level_number, box_size):
        """
        Frontend-like: most runs have no locked plants.
        Add locks only after the solver has reached larger levels.
        """
        locked = []

        if level_number >= 8:
            locked.append(
                {
                    "name": "tomato",
                    "box_index": 0,
                    "row": 0,
                    "col": 0,
                }
            )

        if level_number >= 12:
            locked.append(
                {
                    "name": "carrot",
                    "box_index": 0,
                    "row": box_size // 2,
                    "col": box_size // 2,
                }
            )

        return locked

    def subtract_locked_from_plants(self, plants, locked_plants):
        """
        Mimic the frontend more closely:
        buildAutosortPlantsPayload excludes locked plants, while
        buildLockedPlantsPayload sends locked plants separately.
        """
        counts = {
            item["name"]: item["amount"]
            for item in plants
        }

        for locked in locked_plants:
            name = locked["name"]
            if name in counts:
                counts[name] = max(0, counts[name] - 1)

        return [
            {"name": name, "amount": amount}
            for name, amount in counts.items()
            if amount > 0
        ]

    def make_payload(self, level_number):
        box_size = self.START_BOX_SIZE + level_number - 1

        all_plants = self.build_dynamic_plants(level_number)
        locked_plants = self.build_locked_plants(level_number, box_size)
        unlocked_plants = self.subtract_locked_from_plants(all_plants, locked_plants)

        return {
            "algorithm": "quick",
            "boxes": [
                {
                    "rows": box_size,
                    "cols": box_size,
                }
            ],
            "plants": deepcopy(unlocked_plants),
            "locked_plants": deepcopy(locked_plants),
            "next_to": self.FORCE_SAME_TOGETHER,
            "avoid": True,
            "fill": self.FILL,
            "force_row": False,
            "force_column": False,
            "maximise_search": False,
            "no_companion_overlap": False,
            "cell_cm": self.CELL_CM,
            "time_limit": self.FRONTEND_TIME_LIMIT,
            "k": 3,
        }

    def run_solver(self, solver_name, level_number, extra_payload=None):
        payload = self.make_payload(level_number)
        payload["algorithm"] = solver_name

        if extra_payload:
            payload.update(extra_payload)

        box_size = payload["boxes"][0]["rows"]
        requested_total = sum(item["amount"] for item in payload["plants"])
        locked_total = len(payload["locked_plants"])
        type_count = len(payload["plants"])

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

        plant_instances = data.get("plant_instances") or []
        not_placed = data.get("not_placed") or []

        if response.status_code != 200:
            note = "failed"
        elif len(plant_instances) == 0:
            note = "empty"
        elif len(not_placed) > 0:
            note = "partial"
        else:
            note = "complete"

        row = {
            "solver": solver_name,
            "level": level_number,
            "box_size": box_size,
            "type_count": type_count,
            "requested_total": requested_total,
            "locked_total": locked_total,
            "http_status": response.status_code,
            "score": data.get("total_score"),
            "placed": len(plant_instances),
            "not_placed": len(not_placed),
            "runtime": runtime,
            "note": note,
            "raw": data,
        }

        self.__class__.benchmark_rows.append(row)
        return row

    def run_until_limit(
        self,
        solver_name,
        max_levels,
        extra_payload=None,
        stop_after_seconds=60,
        require_first_success=True,
        stop_on_empty=True,
        stop_on_partial_ratio=0.75,
    ):
        rows = []

        for level_number in range(1, max_levels + 1):
            row = self.run_solver(
                solver_name=solver_name,
                level_number=level_number,
                extra_payload=extra_payload,
            )

            rows.append(row)

            self.assertNotEqual(
                row["http_status"],
                500,
                msg=f"{solver_name} crashed at level {level_number}: {row['raw']}",
            )

            if level_number == 1 and require_first_success:
                self.assertEqual(
                    row["http_status"],
                    200,
                    msg=f"{solver_name} failed at level 1: {row['raw']}",
                )

                self.assertGreater(
                    row["placed"],
                    0,
                    msg=f"{solver_name} placed no plants at level 1",
                )

                self.assertIsNotNone(
                    row["score"],
                    msg=f"{solver_name} did not return a score at level 1",
                )

            if row["http_status"] != 200:
                break

            if row["runtime"] >= stop_after_seconds:
                break

            if stop_on_empty and row["placed"] == 0:
                break

            if stop_on_partial_ratio is not None and row["requested_total"] > 0:
                not_placed_ratio = row["not_placed"] / row["requested_total"]
                if not_placed_ratio >= stop_on_partial_ratio:
                    break

        return rows

    def test_01_quick_find_limit(self):
        self.run_until_limit(
            solver_name="quick",
            max_levels=45,
            extra_payload={
                "time_limit": self.FRONTEND_TIME_LIMIT,
                "fill": False,
            },
            stop_after_seconds=60,
            require_first_success=True,
        )

    def test_02_backtracking_find_limit(self):
        self.run_until_limit(
            solver_name="backtracking_k",
            max_levels=25,
            extra_payload={
                "k": 3,
                "time_limit": self.FRONTEND_TIME_LIMIT,
                "fill": False,
            },
            stop_after_seconds=60,
            require_first_success=True,
        )

    def test_03_constraint_find_limit(self):
        self.run_until_limit(
            solver_name="constraint",
            max_levels=20,
            extra_payload={
                "time_limit": self.FRONTEND_TIME_LIMIT,
                "maximise_search": False,
                "fill": False,
            },
            stop_after_seconds=60,
            require_first_success=True,
        )