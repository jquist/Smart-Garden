import time
from collections import Counter

from django.core.management.base import BaseCommand


DEFAULT_OPTIONS = {
    "next_to": True,
    "avoid": True,
    "fill": False,
    "force_row": False,
    "force_column": False,
    "no_companion_overlap": False,
    "maximise_search": False,
    "cell_cm": 15,
    "time_limit": 12,
    "phantom_box_optimise": True,
}

ALGORITHMS = [
    # label, backend algorithm name, solver internal time_limit in seconds
    ("quick", "quick", 10),
    ("medium", "backtracking_k", 60),
    ("slow", "constraint", 300),
    ("slow_optimal", "constraint", 3600),
]



def cell_to_list(cell):
    if cell == "" or cell is None:
        return []
    if isinstance(cell, list):
        return cell[:]
    return [cell]


def add_to_cell(grid, row, col, name):
    existing = cell_to_list(grid[row][col])
    if name not in existing:
        existing.append(name)

    if len(existing) == 0:
        grid[row][col] = ""
    elif len(existing) == 1:
        grid[row][col] = existing[0]
    else:
        grid[row][col] = existing[:2]


def build_grid_from_instances(box, instances):
    grid = [["" for _ in range(box["cols"])] for _ in range(box["rows"])]

    for inst in instances:
        if int(inst.get("box_index", 0)) != int(box["box_index"]):
            continue

        name = inst["name"]
        row = int(inst["row"])
        col = int(inst["col"])
        height = int(inst.get("height", 1))
        width = int(inst.get("width", 1))

        for r in range(row, row + height):
            for c in range(col, col + width):
                if 0 <= r < box["rows"] and 0 <= c < box["cols"]:
                    add_to_cell(grid, r, c, name)

    return grid


def score_instances(layout, instances, options):
    from Plant_plotter.solvers.constraint_solver import (
        build_plant_lookup_from_db,
        total_score_grid,
    )

    names = sorted({inst["name"] for inst in instances})
    if not names:
        return 0

    plants = build_plant_lookup_from_db(options["cell_cm"], names)

    total = 0
    boxes = [
        {
            "box_index": index,
            "rows": box["rows"],
            "cols": box["cols"],
        }
        for index, box in enumerate(layout["boxes"])
    ]

    for box in boxes:
        grid = build_grid_from_instances(box, instances)
        total += total_score_grid(
            plants=plants,
            grid=grid,
            avoid=options["avoid"],
            next_to=options["next_to"],
            fill=options["fill"],
            force_row=options["force_row"],
            force_column=options["force_column"],
        )

    return total


def count_reference_plants(reference_instances):
    counts = Counter()
    for item in reference_instances:
        if not item.get("locked", False):
            counts[item["name"]] += 1
    return [{"name": name, "amount": amount} for name, amount in sorted(counts.items())]


def locked_from_reference(reference_instances):
    locked = []
    for item in reference_instances:
        if item.get("locked", False):
            locked.append(
                {
                    "name": item["name"],
                    "box_index": item["box_index"],
                    "row": item["row"],
                    "col": item["col"],
                    "width": item.get("width", 1),
                    "height": item.get("height", 1),
                }
            )
    return locked


def validate_instances(layout, instances):
    errors = []

    for inst in instances:
        box_index = int(inst.get("box_index", -1))
        if box_index < 0 or box_index >= len(layout["boxes"]):
            errors.append(f"{inst.get('name')} has invalid box_index {box_index}")
            continue

        box = layout["boxes"][box_index]
        row = int(inst.get("row", 0))
        col = int(inst.get("col", 0))
        height = int(inst.get("height", 1))
        width = int(inst.get("width", 1))

        if row < 0 or col < 0 or row + height > box["rows"] or col + width > box["cols"]:
            errors.append(f"{inst.get('name')} is outside box {box_index}")

    return errors


def get_result_instances(result):
    if not isinstance(result, dict):
        return []

    for key in ("plant_instances", "plants", "placements"):
        value = result.get(key)
        if isinstance(value, list):
            return value

    return []



def run_frontend_like(payload):
    """Run like the frontend/API path: direct run_autosort(payload).

    No external wall timeout is used. Only payload["time_limit"] controls
    solvers that support an internal time limit.
    """
    from Plant_plotter.autosort_service import run_autosort

    start = time.perf_counter()
    try:
        result = run_autosort(payload)
        elapsed = time.perf_counter() - start
        return {
            "status": "OK",
            "elapsed": elapsed,
            "result": result,
            "error": "",
        }
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return {
            "status": "ERROR",
            "elapsed": elapsed,
            "result": None,
            "error": str(exc),
        }


LAYOUTS = [
    {
        "name": "A_medium_companion_garden",
        "target": 115,
        "description": "One medium bed with companion groups and repeated same-type clusters.",
        "boxes": [{"rows": 10, "cols": 10}],
        "reference": [
            {"name": "tomato", "box_index": 0, "row": 0, "col": 0, "width": 3, "height": 3},
            {"name": "basil", "box_index": 0, "row": 0, "col": 0, "width": 2, "height": 2},
            {"name": "parsley", "box_index": 0, "row": 0, "col": 3, "width": 2, "height": 2},
            {"name": "asparagus", "box_index": 0, "row": 3, "col": 0, "width": 3, "height": 3},
            {"name": "carrot", "box_index": 0, "row": 6, "col": 0, "width": 2, "height": 2},
            {"name": "carrot", "box_index": 0, "row": 6, "col": 2, "width": 2, "height": 2},
            {"name": "lettuce", "box_index": 0, "row": 6, "col": 0, "width": 2, "height": 2},
            {"name": "lettuce", "box_index": 0, "row": 6, "col": 2, "width": 2, "height": 2},
            {"name": "onion", "box_index": 0, "row": 8, "col": 0, "width": 2, "height": 2},
            {"name": "onion", "box_index": 0, "row": 8, "col": 2, "width": 2, "height": 2},
        ],
    },
    {
        "name": "B_avoid_heavy_garden",
        "target":85,
        "description": "Avoid relationships force separation while still allowing companion scoring.",
        "boxes": [{"rows": 12, "cols": 10}],
        "reference": [
            {"name": "carrot", "box_index": 0, "row": 0, "col": 0, "width": 2, "height": 2},
            {"name": "carrot", "box_index": 0, "row": 0, "col": 2, "width": 2, "height": 2},
            {"name": "lettuce", "box_index": 0, "row": 0, "col": 0, "width": 2, "height": 2},
            {"name": "onion", "box_index": 0, "row": 2, "col": 0, "width": 2, "height": 2},
            {"name": "garlic", "box_index": 0, "row": 2, "col": 2, "width": 2, "height": 2},
            {"name": "dill", "box_index": 0, "row": 7, "col": 0, "width": 2, "height": 2},
            {"name": "cabbage", "box_index": 0, "row": 7, "col": 2, "width": 3, "height": 3},
            {"name": "broccoli", "box_index": 0, "row": 9, "col": 5, "width": 2, "height": 2},
            {"name": "pea", "box_index": 0, "row": 0, "col": 7, "width": 3, "height": 3},
        ],
    },
    {
        "name": "C_multi_box_locked_garden",
        "target":105,
        "description": "Several beds with locked anchor plants.",
        "boxes": [{"rows": 8, "cols": 8}, {"rows": 6, "cols": 10}, {"rows": 5, "cols": 12}],
        "reference": [
            {"name": "tomato", "box_index": 0, "row": 0, "col": 0, "width": 3, "height": 3, "locked": True},
            {"name": "basil", "box_index": 0, "row": 0, "col": 0, "width": 2, "height": 2},
            {"name": "parsley", "box_index": 0, "row": 0, "col": 3, "width": 2, "height": 2},
            {"name": "carrot", "box_index": 1, "row": 0, "col": 0, "width": 2, "height": 2, "locked": True},
            {"name": "lettuce", "box_index": 1, "row": 0, "col": 0, "width": 2, "height": 2},
            {"name": "onion", "box_index": 1, "row": 2, "col": 0, "width": 2, "height": 2},
            {"name": "garlic", "box_index": 1, "row": 2, "col": 2, "width": 2, "height": 2},
            {"name": "asparagus", "box_index": 2, "row": 0, "col": 0, "width": 3, "height": 3},
            {"name": "coriander", "box_index": 2, "row": 0, "col": 3, "width": 2, "height": 2},
            {"name": "basil", "box_index": 2, "row": 2, "col": 3, "width": 2, "height": 2},
        ],
    },
    {
        "name": "D_dense_high_complexity_garden",
        "target":125,
        "description": "A messy realistic design with many plant types and competing relationships.",
        "boxes": [{"rows": 14, "cols": 14}],
        "reference": [
            {"name": "tomato", "box_index": 0, "row": 0, "col": 0, "width": 3, "height": 3},
            {"name": "basil", "box_index": 0, "row": 0, "col": 0, "width": 2, "height": 2},
            {"name": "oregano", "box_index": 0, "row": 0, "col": 3, "width": 2, "height": 2},
            {"name": "bell pepper", "box_index": 0, "row": 3, "col": 0, "width": 3, "height": 3},
            {"name": "carrot", "box_index": 0, "row": 7, "col": 0, "width": 2, "height": 2},
            {"name": "carrot", "box_index": 0, "row": 7, "col": 2, "width": 2, "height": 2},
            {"name": "lettuce", "box_index": 0, "row": 7, "col": 0, "width": 2, "height": 2},
            {"name": "lettuce", "box_index": 0, "row": 7, "col": 2, "width": 2, "height": 2},
            {"name": "onion", "box_index": 0, "row": 9, "col": 0, "width": 2, "height": 2},
            {"name": "garlic", "box_index": 0, "row": 9, "col": 2, "width": 2, "height": 2},
            {"name": "dill", "box_index": 0, "row": 0, "col": 9, "width": 2, "height": 2},
            {"name": "cabbage", "box_index": 0, "row": 2, "col": 9, "width": 3, "height": 3},
            {"name": "broccoli", "box_index": 0, "row": 5, "col": 9, "width": 2, "height": 2},
            {"name": "beetroot", "box_index": 0, "row": 9, "col": 6, "width": 2, "height": 2},
            {"name": "parsley", "box_index": 0, "row": 4, "col": 4, "width": 2, "height": 2},
        ],
    },
]


class Command(BaseCommand):
    help = "Compare autosort solvers against predefined realistic reference layouts."

    def add_arguments(self, parser):
        parser.add_argument("--layout", default="all", help="Layout name to run, or 'all'.")
        parser.add_argument("--row", action="store_true", help="Run with force_row=True.")
        parser.add_argument("--column", action="store_true", help="Run with force_column=True.")
        parser.add_argument("--max-spread", action="store_true", help="Run fill/max-spread algorithm variants.")
        parser.add_argument("--no-companion-overlap", action="store_true", help="Disallow companion overlap.")
        parser.add_argument("--timeout", type=int, default=3600, help="Maximum solver internal time_limit allowed per layout/solver in seconds.")
        parser.add_argument(
            "--target",
            choices=["known", "reference"],
            default="known",
            help="'known' uses the manual benchmark target stored in each layout. 'reference' uses only the hand-made layout score.",
        )

    def handle(self, *args, **options):
        selected_layout = options["layout"]
        timeout_seconds = int(options["timeout"])

        run_options = dict(DEFAULT_OPTIONS)
        if options["row"]:
            run_options["force_row"] = True
            run_options["force_column"] = False
        if options["column"]:
            run_options["force_column"] = True
            run_options["force_row"] = False
        if options["no_companion_overlap"]:
            run_options["no_companion_overlap"] = True
        if options["max_spread"]:
            run_options["fill"] = True

        layouts = [layout for layout in LAYOUTS if selected_layout == "all" or layout["name"] == selected_layout]

        if not layouts:
            self.stderr.write(self.style.ERROR(f"No layout found called {selected_layout!r}"))
            return

        from Plant_plotter.models import Plant

        all_names = sorted({item["name"] for layout in layouts for item in layout["reference"]})
        missing = sorted(set(all_names) - set(Plant.objects.filter(name__in=all_names).values_list("name", flat=True)))
        if missing:
            self.stderr.write(self.style.ERROR("Missing plants in database: " + ", ".join(missing)))
            return

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Solver benchmark comparison frontend-like"))
        self.stdout.write("Target mode: " + ("manual benchmark" if options["target"] == "known" else "reference layout score"))
        self.stdout.write(
            f"Options: next_to={run_options['next_to']}, avoid={run_options['avoid']}, "
            f"fill={run_options['fill']}, row={run_options['force_row']}, "
            f"column={run_options['force_column']}, no_companion_overlap={run_options['no_companion_overlap']}, "
            f"max_solver_time_limit={timeout_seconds}s, external_wall_timeout=off"
        )
        self.stdout.write("")

        header = (
            f"{'Layout':35} {'Solver':12} {'Score':>8} {'Target':>8} "
            f"{'%Target':>9} {'Time(s)':>9} {'Placed':>8} {'NotPlaced':>10} {'Status':>9} {'Valid':>7}"
        )
        self.stdout.write(header)
        self.stdout.write("-" * len(header))

        for layout in layouts:
            reference_score = score_instances(layout, layout["reference"], run_options)
            locked_count = len([x for x in layout["reference"] if x.get("locked", False)])
            solver_rows = []

            for solver_label, algorithm, default_timeout in ALGORITHMS:
                resolved_algorithm = algorithm
                if options["max_spread"]:
                    if algorithm == "quick":
                        resolved_algorithm = "quick_fill"
                    elif algorithm == "backtracking_k":
                        resolved_algorithm = "backtracking_minmax"
                    elif algorithm == "constraint":
                        resolved_algorithm = "constraint_fill"

                payload = {
                    **run_options,
                    "algorithm": resolved_algorithm,
                    "boxes": layout["boxes"],
                    "plants": count_reference_plants(layout["reference"]),
                    "locked_plants": locked_from_reference(layout["reference"]),
                    "k": 3,
                    "cell_cm": 15,
                    "time_limit": min(timeout_seconds, default_timeout),
                    "phantom_box_optimise": True,
                }

                if solver_label == "slow_optimal":
                    payload["maximise_search"] = True
                    payload["time_limit"] = min(timeout_seconds, 3600)

                result_data = run_frontend_like(payload)
                row = {
                    "layout": layout,
                    "solver_label": solver_label,
                    "status": result_data["status"],
                    "elapsed": result_data["elapsed"],
                    "score": None,
                    "placed": 0,
                    "not_placed": 0,
                    "valid": "no",
                    "error": result_data["error"],
                }

                if result_data["status"] == "OK":
                    result = result_data["result"]
                    instances = get_result_instances(result)
                    row["score"] = score_instances(layout, instances, run_options)
                    row["not_placed"] = len(result.get("not_placed", [])) if isinstance(result, dict) else 0
                    row["placed"] = len([x for x in instances if not x.get("locked", False)]) + locked_count
                    row["valid_errors"] = validate_instances(layout, instances)
                    row["valid"] = "yes" if not row["valid_errors"] else "no"
                else:
                    row["valid_errors"] = [result_data["error"]]

                solver_rows.append(row)

            target_score = reference_score if options["target"] == "reference" else layout.get("target", reference_score)

            for row in solver_rows:
                score = row["score"]
                percent_text = "-"
                score_text = "ERROR" if score is None else f"{score:.1f}"
                if isinstance(score, (int, float)) and target_score != 0:
                    percent_text = f"{(score / target_score) * 100:.1f}%"

                self.stdout.write(
                    f"{layout['name'][:35]:35} {row['solver_label']:12} "
                    f"{score_text:>8} {target_score:8.1f} "
                    f"{percent_text:>9} {row['elapsed']:9.3f} "
                    f"{row['placed']:8} {row['not_placed']:10} {row['status']:>9} {row['valid']:>7}"
                )

                if row["status"] != "OK":
                    self.stdout.write(f"  - {row['error']}")

            if options["target"] == "known":
                self.stdout.write(
                    f"  Manual benchmark target {target_score:.1f}; reference layout score {reference_score:.1f}."
                )

            self.stdout.write("")
