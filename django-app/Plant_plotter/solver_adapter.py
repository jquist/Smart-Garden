# solver_adapter.py

from math import ceil
from .models import Plant, Companion_helpslistItem, Companion_helped_bylistItem, Plants_avoidlistItem

CELL_SIZE_CM = 15
BLOCKED = "#"
EMPTY = ""


def cm_to_cells(value_cm):
    """
    Convert a spacing in cm into grid cells based on a 15cm x 15cm cell.
    Always returns at least 1 cell.
    """
    if value_cm is None:
        return 1

    try:
        value = float(value_cm)
    except (TypeError, ValueError):
        return 1

    return max(1, round(value / CELL_SIZE_CM))


def build_solver_plant(plant):
    """
    Convert a Plant model instance into the dict format the solver expects.
    """
    helps = list(
        Companion_helpslistItem.objects.filter(plant=plant)
        .select_related("other_plant")
        .values_list("other_plant__name", flat=True)
    )

    helps_by = list(
        Companion_helped_bylistItem.objects.filter(plant=plant)
        .select_related("other_plant")
        .values_list("other_plant__name", flat=True)
    )

    avoid = list(
        Plants_avoidlistItem.objects.filter(plant=plant)
        .select_related("other_plant")
        .values_list("other_plant__name", flat=True)
    )

    return {
        "name": plant.name.lower(),
        "size": cm_to_cells(plant.spacing_between_rows),
        "size_same": cm_to_cells(plant.spacing_in_rows),
        "helps": [x.lower() for x in helps],
        "helps_by": [x.lower() for x in helps_by],
        "avoid": [x.lower() for x in avoid],
    }


def build_solver_plants_map(plant_counts):
    """
    plant_counts format expected:
    [
        {"plant_id": 1, "count": 2},
        {"plant_id": 5, "count": 4}
    ]

    Returns:
    {
        "tomato": {...solver dict...},
        "basil": {...solver dict...}
    }
    """
    plants_map = {}

    for item in plant_counts:
        plant_id = item.get("plant_id")
        count = int(item.get("count", 0))

        if count <= 0:
            continue

        plant = Plant.objects.get(id=plant_id)
        solver_plant = build_solver_plant(plant)
        plants_map[solver_plant["name"]] = solver_plant

    return plants_map


def build_solver_list(plant_counts, plants_map):
    """
    Build the solver list format:
    [
        [plant_dict, count],
        [plant_dict, count]
    ]
    """
    output = []

    for item in plant_counts:
        plant_id = item.get("plant_id")
        count = int(item.get("count", 0))

        if count <= 0:
            continue

        plant = Plant.objects.get(id=plant_id)
        plant_name = plant.name.lower()

        if plant_name in plants_map:
            output.append([plants_map[plant_name], count])

    return output


def get_board_dimensions(boxes):
    """
    boxes format:
    [
        {"x": 0, "y": 0, "w": 4, "h": 4},
        {"x": 6, "y": 0, "w": 3, "h": 5}
    ]
    """
    if not boxes:
        return 0, 0

    max_x = max(box["x"] + box["w"] for box in boxes)
    max_y = max(box["y"] + box["h"] for box in boxes)

    return max_y, max_x  # rows, cols


def point_in_any_box(x, y, boxes):
    for box in boxes:
        if (
            box["x"] <= x < box["x"] + box["w"]
            and box["y"] <= y < box["y"] + box["h"]
        ):
            return True
    return False


def build_base_grid(boxes):
    """
    Create a rectangular grid covering all boxes.
    Cells inside a box are EMPTY.
    Cells outside all boxes are BLOCKED.
    """
    rows, cols = get_board_dimensions(boxes)

    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            if point_in_any_box(x, y, boxes):
                row.append(EMPTY)
            else:
                row.append(BLOCKED)
        grid.append(row)

    return grid


def normalise_grid_for_solver(grid):
    """
    If your solver absolutely cannot handle blocked cells yet,
    this keeps a copy ready for future use.

    For now, returns the grid as-is.
    """
    return [row[:] for row in grid]


def build_solver_input(payload):
    """
    Convert incoming API payload into everything needed by the solver.
    """
    boxes = payload.get("boxes", [])
    plant_counts = payload.get("plants", [])
    options = payload.get("options", {})

    plants_map = build_solver_plants_map(plant_counts)
    solver_list = build_solver_list(plant_counts, plants_map)
    base_grid = build_base_grid(boxes)

    return {
        "plants_map": plants_map,
        "solver_list": solver_list,
        "base_grid": normalise_grid_for_solver(base_grid),
        "boxes": boxes,
        "options": {
            "avoidSpacing": bool(options.get("avoidSpacing", False)),
            "forceSameTogether": bool(options.get("forceSameTogether", False)),
            "fill": bool(options.get("fill", False)),
        },
    }