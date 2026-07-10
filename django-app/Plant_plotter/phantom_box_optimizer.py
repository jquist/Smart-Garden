import math
from copy import deepcopy

from .models import Plant


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _plant_size_cells(plant_name, cell_cm):
    """Return the full spacing footprint size in grid cells.

    This deliberately uses spacing_between_rows, not spacing_in_rows, because
    the phantom estimate is based on the max-spread/full-spacing footprint.
    """
    try:
        plant = Plant.objects.get(name=plant_name)
    except Plant.DoesNotExist:
        return 1

    spacing_cm = _to_int(getattr(plant, "spacing_between_rows", 0), 0)
    return max(1, math.ceil(spacing_cm / max(1, cell_cm)))


def _estimate_full_spacing_area(payload):
    cell_cm = max(1, _to_int(payload.get("cell_cm"), 15))
    total_area = 0
    biggest_size = 1

    for item in payload.get("plants", []) or []:
        name = item.get("name")
        amount = max(0, _to_int(item.get("amount"), 0))
        if not name or amount <= 0:
            continue

        size = _plant_size_cells(name, cell_cm)
        biggest_size = max(biggest_size, size)
        total_area += amount * size * size

    for locked in payload.get("locked_plants", []) or []:
        width = max(1, _to_int(locked.get("width"), 1))
        height = max(1, _to_int(locked.get("height"), 1))
        biggest_size = max(biggest_size, width, height)
        total_area += width * height

    return max(1, total_area), biggest_size


def _buffer_multiplier(payload):
    multiplier = 1.35

    # Avoid halos and row/column preferences need spare space, otherwise the
    # phantom box becomes too optimistic and can create false failures.
    if bool(payload.get("avoid", False)):
        multiplier += 0.25
    if bool(payload.get("fill", False)):
        multiplier += 0.45
    if bool(payload.get("force_row", False)) or bool(payload.get("force_column", False)):
        multiplier += 0.25
    if payload.get("locked_plants"):
        multiplier += 0.15
    if bool(payload.get("maximise_search", False)):
        multiplier += 0.15

    return multiplier


def _locked_required_extent(locked_plants, box_index):
    """Minimum rows/cols needed so locked plants remain inside a phantom box."""
    min_rows = 1
    min_cols = 1

    for locked in locked_plants or []:
        if _to_int(locked.get("box_index"), -1) != box_index:
            continue

        row = max(0, _to_int(locked.get("row"), 0))
        col = max(0, _to_int(locked.get("col"), 0))
        height = max(1, _to_int(locked.get("height"), 1))
        width = max(1, _to_int(locked.get("width"), 1))

        min_rows = max(min_rows, row + height)
        min_cols = max(min_cols, col + width)

    return min_rows, min_cols


def _make_phantom_box(box, target_area, biggest_size, locked_min_rows, locked_min_cols):
    original_rows = max(1, _to_int(box.get("rows"), 1))
    original_cols = max(1, _to_int(box.get("cols"), 1))
    original_area = original_rows * original_cols

    if target_area >= original_area:
        return {"rows": original_rows, "cols": original_cols}

    ratio = original_cols / max(1, original_rows)
    phantom_cols = max(1, math.ceil(math.sqrt(target_area * ratio)))
    phantom_rows = max(1, math.ceil(target_area / phantom_cols))

    min_rows = max(biggest_size, locked_min_rows)
    min_cols = max(biggest_size, locked_min_cols)

    phantom_rows = max(min_rows, phantom_rows)
    phantom_cols = max(min_cols, phantom_cols)

    # Keep the phantom inside the real box. If locked plants already require the
    # full real dimension, this naturally disables shrinking on that axis.
    phantom_rows = min(original_rows, phantom_rows)
    phantom_cols = min(original_cols, phantom_cols)

    # If rounding/minimums made the area too small, expand the dimension that
    # best preserves the original aspect ratio until the target is reached.
    while phantom_rows * phantom_cols < target_area and (
        phantom_rows < original_rows or phantom_cols < original_cols
    ):
        current_ratio = phantom_cols / max(1, phantom_rows)

        if current_ratio < ratio and phantom_cols < original_cols:
            phantom_cols += 1
        elif phantom_rows < original_rows:
            phantom_rows += 1
        elif phantom_cols < original_cols:
            phantom_cols += 1
        else:
            break

    return {"rows": phantom_rows, "cols": phantom_cols}


def optimise_payload_boxes(payload):
    """Return a copy of payload with internally shrunken phantom boxes.

    The frontend/user boxes are not changed. This only reduces the grid passed
    to the solver so it searches fewer empty cells. If shrinking is not useful
    or unsafe, the original boxes are returned unchanged.
    """
    if payload.get("phantom_box_optimise", True) is False:
        return deepcopy(payload)

    boxes = payload.get("boxes") or []
    if not boxes:
        return deepcopy(payload)

    original_area = sum(
        max(1, _to_int(box.get("rows"), 1)) * max(1, _to_int(box.get("cols"), 1))
        for box in boxes
    )

    estimated_area, biggest_size = _estimate_full_spacing_area(payload)
    target_total_area = max(estimated_area, math.ceil(estimated_area * _buffer_multiplier(payload)))

    # Do not bother shrinking tiny layouts or layouts where savings are small.
    if original_area <= 0 or target_total_area >= original_area * 0.85:
        return deepcopy(payload)

    optimised = deepcopy(payload)
    locked_plants = optimised.get("locked_plants", []) or []
    new_boxes = []

    for index, box in enumerate(boxes):
        rows = max(1, _to_int(box.get("rows"), 1))
        cols = max(1, _to_int(box.get("cols"), 1))
        box_area = rows * cols

        # Distribute required search area across boxes in proportion to their
        # original area, preserving the number/order of boxes and box_index.
        box_target_area = max(1, math.ceil(target_total_area * (box_area / original_area)))
        locked_min_rows, locked_min_cols = _locked_required_extent(locked_plants, index)

        new_boxes.append(
            _make_phantom_box(
                box={"rows": rows, "cols": cols},
                target_area=box_target_area,
                biggest_size=biggest_size,
                locked_min_rows=locked_min_rows,
                locked_min_cols=locked_min_cols,
            )
        )

    new_area = sum(box["rows"] * box["cols"] for box in new_boxes)

    # Safety: if we did not save much, keep the original payload to avoid any
    # chance of losing valid spread placements for minimal speed benefit.
    if new_area >= original_area * 0.9:
        return deepcopy(payload)

    optimised["boxes"] = new_boxes
    optimised["phantom_box_info"] = {
        "enabled": True,
        "original_area": original_area,
        "phantom_area": new_area,
        "estimated_full_spacing_area": estimated_area,
        "buffer_multiplier": _buffer_multiplier(payload),
    }
    return optimised
