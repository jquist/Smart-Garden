import itertools
import json
import unittest
from collections import Counter, defaultdict
from copy import deepcopy
from unittest.mock import patch

from django.db import models
from django.test import TestCase

from .. import autosort_service
from ..models import (
    Plant,
    Companion_helpslistItem,
    Plants_avoidlistItem,
)
from ..solvers.constraint_solver import (
    build_plant_lookup_from_db,
    relation_score,
    total_score_grid,
)

try:
    from ..management.commands.solver_benchmark import (
        DEFAULT_OPTIONS,
        LAYOUTS,
        count_reference_plants,
        get_result_instances,
        locked_from_reference,
        score_instances,
        validate_instances,
    )
except Exception:  
    DEFAULT_OPTIONS = None
    LAYOUTS = None
    count_reference_plants = None
    get_result_instances = None
    locked_from_reference = None
    score_instances = None
    validate_instances = None


class SolverExtraRegressionTests(TestCase):

    AUTOSORT_URL = "/api/auto-sort/"
    evaluation_rows = []

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        if not cls.evaluation_rows:
            return

        print("\n\nExtra solver evaluation evidence")
        print("-" * 150)
        print(
            f"{'Evidence test':<46}"
            f"{'Result A':<32}"
            f"{'Result B':<32}"
            f"{'Placed':<16}"
            f"{'Not placed':<16}"
            f"{'Conclusion':<8}"
        )
        print("-" * 150)

        for row in cls.evaluation_rows:
            print(
                f"{str(row.get('test', '')):<46}"
                f"{str(row.get('result_a', '')):<32}"
                f"{str(row.get('result_b', '')):<32}"
                f"{str(row.get('placed', '')):<16}"
                f"{str(row.get('not_placed', '')):<16}"
                f"{str(row.get('conclusion', '')):<8}"
            )

        print("-" * 150)

    def record_evaluation_row(
        self,
        test,
        result_a="",
        result_b="",
        placed="",
        not_placed="",
        conclusion="",
    ):
        self.__class__.evaluation_rows.append(
            {
                "test": test,
                "result_a": result_a,
                "result_b": result_b,
                "placed": placed,
                "not_placed": not_placed,
                "conclusion": conclusion,
            }
        )

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
        Companion_helpslistItem.objects.create(plant=plant, other_plant=other)

    def add_avoid(self, plant, other):
        Plants_avoidlistItem.objects.create(plant=plant, other_plant=other)

    def setUp(self):
        self.carrot = self.create_plant("carrot")
        self.lettuce = self.create_plant("lettuce")
        self.tomato = self.create_plant("tomato")
        self.basil = self.create_plant("basil")
        self.dill = self.create_plant("dill")
        self.radish = self.create_plant("radish")
        self.onion = self.create_plant("onion")
        self.garlic = self.create_plant("garlic")

        self.add_helps(self.carrot, self.lettuce)
        self.add_helps(self.lettuce, self.carrot)
        self.add_helps(self.tomato, self.basil)
        self.add_helps(self.basil, self.tomato)
        self.add_helps(self.carrot, self.onion)
        self.add_helps(self.onion, self.carrot)
        self.add_helps(self.garlic, self.lettuce)
        self.add_helps(self.lettuce, self.garlic)

        self.add_avoid(self.carrot, self.dill)
        self.add_avoid(self.dill, self.carrot)

    def post_autosort(self, payload):
        response = self.client.post(
            self.AUTOSORT_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, msg=response.content.decode())
        return response.json()

    def base_payload(self, extra=None):
        payload = {
            "algorithm": "quick",
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
            "phantom_box_optimise": False,
            "cell_cm": 15,
            "time_limit": 5,
            "k": 3,
        }
        if extra:
            payload.update(deepcopy(extra))
        return payload

    def add_to_cell(self, grid, row, col, name):
        existing = grid[row][col]
        if existing == "" or existing is None:
            grid[row][col] = name
            return
        if not isinstance(existing, list):
            existing = [existing]
        if name not in existing:
            existing.append(name)
        grid[row][col] = existing[:2]

    def grid_from_instances(self, boxes, instances):
        grids = []
        for box_index, box in enumerate(boxes):
            grid = [["" for _ in range(box["cols"])] for _ in range(box["rows"])]
            for inst in instances:
                if int(inst.get("box_index", 0)) != box_index:
                    continue
                for r in range(inst["row"], inst["row"] + inst.get("height", 1)):
                    for c in range(inst["col"], inst["col"] + inst.get("width", 1)):
                        self.assertGreaterEqual(r, 0)
                        self.assertGreaterEqual(c, 0)
                        self.assertLess(r, box["rows"])
                        self.assertLess(c, box["cols"])
                        self.add_to_cell(grid, r, c, inst["name"])
            grids.append(grid)
        return grids

    def score_layout_instances(self, boxes, instances, options=None):
        options = options or self.base_payload()
        names = sorted({item["name"] for item in instances})
        if not names:
            return 0
        plants = build_plant_lookup_from_db(options.get("cell_cm", 15), names)
        return sum(
            total_score_grid(
                plants=plants,
                grid=grid,
                avoid=options.get("avoid", True),
                next_to=options.get("next_to", True),
                fill=options.get("fill", False),
                force_row=options.get("force_row", False),
                force_column=options.get("force_column", False),
            )
            for grid in self.grid_from_instances(boxes, instances)
        )

    def occupied_cells(self, instances):
        cells = defaultdict(list)
        for inst in instances:
            for r in range(inst["row"], inst["row"] + inst.get("height", 1)):
                for c in range(inst["col"], inst["col"] + inst.get("width", 1)):
                    cells[(inst.get("box_index", 0), r, c)].append(inst["name"])
        return cells

    def cells_for_instance(self, inst):
        return {
            (
                int(inst.get("box_index", 0)),
                int(inst.get("row", 0)) + r,
                int(inst.get("col", 0)) + c,
            )
            for r in range(int(inst.get("height", 1)))
            for c in range(int(inst.get("width", 1)))
        }

    def same_type_axis_contacts(self, instances, plant_name):
        """Count side contacts between separate instances of the same plant type.

        Horizontal contacts mean left/right touching, which is what the row
        forcing option should prefer. Vertical contacts mean top/bottom touching,
        which is what the column forcing option should prefer.
        """
        selected = [item for item in instances if item.get("name") == plant_name]
        horizontal = 0
        vertical = 0

        for index, plant_a in enumerate(selected):
            cells_a = self.cells_for_instance(plant_a)
            for plant_b in selected[index + 1:]:
                cells_b = self.cells_for_instance(plant_b)
                for box_index, row, col in cells_a:
                    if (box_index, row, col - 1) in cells_b or (box_index, row, col + 1) in cells_b:
                        horizontal += 1
                    if (box_index, row - 1, col) in cells_b or (box_index, row + 1, col) in cells_b:
                        vertical += 1

        return horizontal, vertical

    def names_count(self, instances):
        return Counter(item["name"] for item in instances)

    def assert_instances_inside_boxes(self, boxes, instances):
        for inst in instances:
            box_index = int(inst.get("box_index", -1))
            self.assertGreaterEqual(box_index, 0, msg=inst)
            self.assertLess(box_index, len(boxes), msg=inst)
            box = boxes[box_index]
            self.assertGreaterEqual(int(inst.get("row", 0)), 0, msg=inst)
            self.assertGreaterEqual(int(inst.get("col", 0)), 0, msg=inst)
            self.assertLessEqual(int(inst.get("row", 0)) + int(inst.get("height", 1)), box["rows"], msg=inst)
            self.assertLessEqual(int(inst.get("col", 0)) + int(inst.get("width", 1)), box["cols"], msg=inst)

    def test_solver_matches_bruteforce_optimum_on_tiny_layout(self):
        boxes = [{"rows": 3, "cols": 3}]
        plant_names = ["carrot", "lettuce", "radish"]
        plants = build_plant_lookup_from_db(15, plant_names)

        possible_positions = [(r, c) for r in range(3) for c in range(3)]
        best_score = None
        valid_layout_count = 0
        invalid_layout_count = 0

        for positions in itertools.product(possible_positions, repeat=len(plant_names)):
            instances = [
                {
                    "name": name,
                    "box_index": 0,
                    "row": row,
                    "col": col,
                    "width": 1,
                    "height": 1,
                    "size_same": 1,
                }
                for name, (row, col) in zip(plant_names, positions)
            ]

            self.assert_instances_inside_boxes(boxes, instances)

            is_valid = True
            for names_in_cell in self.occupied_cells(instances).values():
                if len(names_in_cell) > 2:
                    is_valid = False
                    break
                if len(names_in_cell) == 2:
                    a, b = names_in_cell
                    if relation_score(plants, a, b) <= 0:
                        is_valid = False
                        break

            if not is_valid:
                invalid_layout_count += 1
                continue

            valid_layout_count += 1
            score = self.score_layout_instances(boxes, instances)
            best_score = score if best_score is None else max(best_score, score)

        self.assertGreater(valid_layout_count, 0)
        self.assertGreater(invalid_layout_count, 0)
        self.assertIsNotNone(best_score)

        payload = self.base_payload(
            {
                "algorithm": "quick",
                "boxes": boxes,
                "plants": [
                    {"name": "carrot", "amount": 1},
                    {"name": "lettuce", "amount": 1},
                    {"name": "radish", "amount": 1},
                ],
            }
        )
        data = self.post_autosort(payload)
        instances = data.get("plant_instances", [])

        solver_score = self.score_layout_instances(boxes, instances, payload)

        self.assertEqual(len(instances), 3)
        self.assertEqual(self.names_count(instances), Counter(plant_names))
        self.assertEqual(solver_score, best_score)

        self.record_evaluation_row(
            test="Tiny brute-force optimum",
            result_a=f"brute optimum={best_score}",
            result_b=f"quick score={solver_score}",
            placed=len(instances),
            not_placed=len(data.get("not_placed", [])),
            conclusion="match",
        )

    def first_available_baseline(self, boxes, requested):
        instances = []
        occupied = set()

        for item in requested:
            for _ in range(item["amount"]):
                placed = False
                for box_index, box in enumerate(boxes):
                    for row in range(box["rows"]):
                        for col in range(box["cols"]):
                            if (box_index, row, col) in occupied:
                                continue
                            instances.append(
                                {
                                    "name": item["name"],
                                    "box_index": box_index,
                                    "row": row,
                                    "col": col,
                                    "width": 1,
                                    "height": 1,
                                    "size_same": 1,
                                }
                            )
                            occupied.add((box_index, row, col))
                            placed = True
                            break
                        if placed:
                            break
                    if placed:
                        break
        return instances

    def test_quick_solver_scores_above_first_available_baseline(self):
        boxes = [{"rows": 5, "cols": 5}]
        requested = [
            {"name": "carrot", "amount": 2},
            {"name": "lettuce", "amount": 2},
            {"name": "tomato", "amount": 1},
            {"name": "basil", "amount": 1},
            {"name": "dill", "amount": 1},
        ]

        payload = self.base_payload(
            {
                "boxes": boxes,
                "plants": requested,
                "algorithm": "quick",
                "next_to": True,
                "avoid": True,
            }
        )

        baseline_instances = self.first_available_baseline(boxes, requested)
        self.assertGreater(len(baseline_instances), 0)

        data = self.post_autosort(payload)
        quick_instances = data.get("plant_instances", [])

        baseline_score = self.score_layout_instances(boxes, baseline_instances, payload)
        quick_score = self.score_layout_instances(boxes, quick_instances, payload)

        self.assertGreaterEqual(len(quick_instances), len(baseline_instances))
        self.assertGreaterEqual(quick_score, baseline_score)

        self.record_evaluation_row(
            test="Naive baseline comparison",
            result_a=f"baseline score={baseline_score}",
            result_b=f"quick score={quick_score}",
            placed=f"baseline={len(baseline_instances)}, quick={len(quick_instances)}",
            not_placed=len(data.get("not_placed", [])),
            conclusion="quick>=base",
        )

    def test_locked_plants_are_not_counted_twice(self):
        payload = self.base_payload(
            {
                "boxes": [{"rows": 6, "cols": 6}],
                "plants": [{"name": "tomato", "amount": 1}],
                "locked_plants": [
                    {"name": "tomato", "box_index": 0, "row": 0, "col": 0},
                ],
            }
        )

        data = self.post_autosort(payload)
        instances = data.get("plant_instances", [])
        tomatoes = [item for item in instances if item.get("name") == "tomato"]
        locked_tomatoes = [item for item in tomatoes if item.get("locked")]

        self.assertEqual(len(tomatoes), 2, msg=data)
        self.assertEqual(len(locked_tomatoes), 1, msg=data)
        self.assertTrue(
            any(
                item.get("box_index") == 0 and item.get("row") == 0 and item.get("col") == 0
                for item in locked_tomatoes
            ),
            msg=data,
        )
        self.assertLessEqual(len(instances), 2)

    def test_dense_layout_reports_unplaced_plants_instead_of_deleting_them(self):
        # Use distinct plant types, not repeated tomatoes. Same-type plants are
        # allowed to share relaxed same-spacing cells in the current solver, so
        # ten 1x1 tomatoes in a 2x2 box is not a reliable impossible case.
        requested = [
            {"name": "carrot", "amount": 1},
            {"name": "lettuce", "amount": 1},
            {"name": "tomato", "amount": 1},
            {"name": "basil", "amount": 1},
            {"name": "radish", "amount": 1},
        ]
        requested_count = sum(item["amount"] for item in requested)
        requested_names = {item["name"] for item in requested}

        payload = self.base_payload(
            {
                "boxes": [{"rows": 2, "cols": 2}],
                "plants": requested,
                "algorithm": "quick",
                "no_companion_overlap": True,
            }
        )

        data = self.post_autosort(payload)
        placed = [
            item for item in data.get("plant_instances", [])
            if item.get("name") in requested_names
        ]
        not_placed = [
            name for name in data.get("not_placed", [])
            if name in requested_names
        ]

        self.assertIsInstance(data.get("plant_instances"), list)
        self.assertIsInstance(data.get("not_placed"), list)
        self.assertGreater(len(not_placed), 0, msg=data)
        self.assertEqual(len(placed) + len(not_placed), requested_count, msg=data)

        for names_in_cell in self.occupied_cells(placed).values():
            self.assertLessEqual(
                len(set(names_in_cell)),
                1,
                msg=f"Different plant types overlapped despite no_companion_overlap=True: {data}",
            )

    def test_phantom_box_failure_falls_back_to_original_boxes(self):
        payload = {
            "algorithm": "quick",
            "boxes": [{"rows": 8, "cols": 8}],
            "plants": [{"name": "carrot", "amount": 1}],
            "locked_plants": [],
            "phantom_box_optimise": True,
        }
        optimised_payload = {
            **payload,
            "boxes": [{"rows": 1, "cols": 1}],
            "phantom_box_info": {"original_boxes": payload["boxes"]},
        }

        def fake_solver(incoming_payload):
            if incoming_payload["boxes"] == optimised_payload["boxes"]:
                return {"plant_instances": [], "not_placed": ["carrot"], "total_score": 0}
            return {
                "plant_instances": [
                    {"name": "carrot", "box_index": 0, "row": 4, "col": 4, "width": 1, "height": 1},
                ],
                "not_placed": [],
                "total_score": 1,
            }

        with patch.object(autosort_service, "optimise_payload_boxes", return_value=optimised_payload), patch.object(
            autosort_service, "_run_selected_solver", side_effect=fake_solver
        ):
            result = autosort_service.run_autosort(payload)

        self.assertEqual(len(result.get("plant_instances", [])), 1)
        self.assertEqual(result.get("not_placed"), [])
        self.assertTrue(result.get("phantom_box_info", {}).get("fallback_used"))
        self.assertEqual(
            result.get("phantom_box_info", {}).get("fallback_reason"),
            "phantom_result_had_unplaced_plants",
        )
        self.assert_instances_inside_boxes(payload["boxes"], result["plant_instances"])

    def test_solver_option_changes_output_under_same_payload(self):
        base = self.base_payload(
            {
                "boxes": [{"rows": 1, "cols": 1}],
                "plants": [
                    {"name": "carrot", "amount": 1},
                    {"name": "lettuce", "amount": 1},
                ],
                "algorithm": "quick",
            }
        )

        overlap_allowed = self.post_autosort({**base, "no_companion_overlap": False})
        overlap_blocked = self.post_autosort({**base, "no_companion_overlap": True})

        self.assertEqual(len(overlap_allowed.get("plant_instances", [])), 2, msg=overlap_allowed)
        self.assertLessEqual(len(overlap_blocked.get("plant_instances", [])), 1, msg=overlap_blocked)

        for names_in_cell in self.occupied_cells(overlap_blocked.get("plant_instances", [])).values():
            self.assertLessEqual(len(set(names_in_cell)), 1)

        self.record_evaluation_row(
            test="No companion overlap ablation",
            result_a=f"allowed placed={len(overlap_allowed.get('plant_instances', []))}",
            result_b=f"blocked placed={len(overlap_blocked.get('plant_instances', []))}",
            placed=f"allowed={len(overlap_allowed.get('plant_instances', []))}, blocked={len(overlap_blocked.get('plant_instances', []))}",
            not_placed=f"blocked={len(overlap_blocked.get('not_placed', []))}",
            conclusion="blocked",
        )

    def test_row_and_column_forcing_change_same_type_axis_preference(self):
        requested = [{"name": "carrot", "amount": 4}]
        base = self.base_payload(
            {
                "algorithm": "constraint",
                "boxes": [{"rows": 4, "cols": 4}],
                "plants": requested,
                "next_to": True,
                "avoid": False,
                "no_companion_overlap": True,
                "time_limit": 3,
                "maximise_search": False,
            }
        )

        row_data = self.post_autosort({**base, "force_row": True, "force_column": False})
        column_data = self.post_autosort({**base, "force_row": False, "force_column": True})

        row_instances = row_data.get("plant_instances", [])
        column_instances = column_data.get("plant_instances", [])

        self.assertEqual(self.names_count(row_instances)["carrot"], 4, msg=row_data)
        self.assertEqual(self.names_count(column_instances)["carrot"], 4, msg=column_data)
        self.assert_instances_inside_boxes(base["boxes"], row_instances)
        self.assert_instances_inside_boxes(base["boxes"], column_instances)

        row_horizontal, row_vertical = self.same_type_axis_contacts(row_instances, "carrot")
        column_horizontal, column_vertical = self.same_type_axis_contacts(column_instances, "carrot")

        self.assertGreater(row_horizontal + row_vertical, 0, msg=row_data)
        self.assertGreater(column_horizontal + column_vertical, 0, msg=column_data)

        self.assertGreaterEqual(
            row_horizontal,
            row_vertical,
            msg=f"force_row should prefer horizontal same-type contacts: {row_data}",
        )
        self.assertGreaterEqual(
            column_vertical,
            column_horizontal,
            msg=f"force_column should prefer vertical same-type contacts: {column_data}",
        )

        self.record_evaluation_row(
            test="Row/column option ablation",
            result_a=f"row H={row_horizontal}, V={row_vertical}",
            result_b=f"column H={column_horizontal}, V={column_vertical}",
            placed=f"row={len(row_instances)}, column={len(column_instances)}",
            not_placed=f"row={len(row_data.get('not_placed', []))}, column={len(column_data.get('not_placed', []))}",
            conclusion="axis ok",
        )

    def test_avoid_relationship_blocks_overlap_regardless_of_direction(self):
        avoid_a = self.create_plant("avoid_a")
        avoid_b = self.create_plant("avoid_b")

        def run_with_one_way_avoid(source, target):
            Plants_avoidlistItem.objects.filter(plant__name__in=["avoid_a", "avoid_b"]).delete()
            Plants_avoidlistItem.objects.create(plant=source, other_plant=target)
            payload = self.base_payload(
                {
                    "algorithm": "quick",
                    "boxes": [{"rows": 1, "cols": 1}],
                    "plants": [
                        {"name": "avoid_a", "amount": 1},
                        {"name": "avoid_b", "amount": 1},
                    ],
                    "avoid": True,
                    "no_companion_overlap": False,
                }
            )
            return self.post_autosort(payload)

        a_avoids_b = run_with_one_way_avoid(avoid_a, avoid_b)
        b_avoids_a = run_with_one_way_avoid(avoid_b, avoid_a)

        for data in (a_avoids_b, b_avoids_a):
            instances = data.get("plant_instances", [])
            self.assertGreaterEqual(len(instances), 1, msg=data)
            self.assertLessEqual(
                len(instances),
                1,
                msg="One-way avoid relationship should prevent both plants sharing a one-cell box.",
            )
            self.assertEqual(
                len(instances) + len(data.get("not_placed", [])),
                2,
                msg=data,
            )

    @unittest.skipIf(LAYOUTS is None, "solver_benchmark command helpers could not be imported")
    def test_predefined_reference_layouts_are_valid_and_scoreable(self):
        self.create_missing_benchmark_plants()
        options = dict(DEFAULT_OPTIONS)

        for layout in LAYOUTS:
            with self.subTest(layout=layout["name"]):
                self.assertGreater(layout.get("target", 0), 0)

                for item in layout["reference"]:
                    for key in ("name", "box_index", "row", "col", "width", "height"):
                        self.assertIn(key, item, msg=f"{layout['name']} missing {key}: {item}")

                self.assertEqual(validate_instances(layout, layout["reference"]), [])
                score = score_instances(layout, layout["reference"], options)
                self.assertIsInstance(score, (int, float))

                locked = locked_from_reference(layout["reference"])
                unlocked = count_reference_plants(layout["reference"])
                self.assertEqual(len(locked), len([x for x in layout["reference"] if x.get("locked", False)]))
                self.assertEqual(
                    sum(item["amount"] for item in unlocked),
                    len([x for x in layout["reference"] if not x.get("locked", False)]),
                )

    @unittest.skipIf(LAYOUTS is None, "solver_benchmark command helpers could not be imported")
    def test_all_benchmark_solver_outputs_stay_inside_boxes(self):
        self.create_missing_benchmark_plants()

        for layout in LAYOUTS:
            with self.subTest(layout=layout["name"]):
                payload = {
                    **DEFAULT_OPTIONS,
                    "algorithm": "quick",
                    "boxes": layout["boxes"],
                    "plants": count_reference_plants(layout["reference"]),
                    "locked_plants": locked_from_reference(layout["reference"]),
                    "k": 3,
                    "cell_cm": 15,
                    "time_limit": 5,
                    "phantom_box_optimise": True,
                }
                result = autosort_service.run_autosort(payload)
                instances = get_result_instances(result)

                self.assertIsInstance(result, dict)
                self.assertGreater(len(instances), 0, msg=result)
                self.assertEqual(validate_instances(layout, instances), [], msg=result)

    def create_missing_benchmark_plants(self):
        names = sorted({item["name"] for layout in LAYOUTS for item in layout["reference"]})
        existing = set(Plant.objects.filter(name__in=names).values_list("name", flat=True))
        for name in names:
            if name not in existing:
                self.create_plant(name)

    def test_solver_treats_relationships_consistently_in_both_directions(self):
        plant_a = self.create_plant("plant_a")
        plant_b = self.create_plant("plant_b")

        def run_one_way_relation(source, target):
            Companion_helpslistItem.objects.filter(plant__name__in=["plant_a", "plant_b"]).delete()
            Companion_helpslistItem.objects.create(plant=source, other_plant=target)
            payload = self.base_payload(
                {
                    "algorithm": "constraint",
                    "boxes": [{"rows": 1, "cols": 1}],
                    "plants": [
                        {"name": "plant_a", "amount": 1},
                        {"name": "plant_b", "amount": 1},
                    ],
                    "time_limit": 3,
                    "maximise_search": False,
                    "no_companion_overlap": False,
                }
            )
            return self.post_autosort(payload)

        a_to_b = run_one_way_relation(plant_a, plant_b)
        b_to_a = run_one_way_relation(plant_b, plant_a)

        self.assertEqual(len(a_to_b.get("plant_instances", [])), 2, msg=a_to_b)
        self.assertGreater(a_to_b.get("total_score", 0), 0, msg=a_to_b)
        self.assertEqual(len(b_to_a.get("plant_instances", [])), 2, msg=b_to_a)
        self.assertGreater(b_to_a.get("total_score", 0), 0, msg=b_to_a)
