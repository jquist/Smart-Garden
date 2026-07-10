import math

from .constraint_solver import (
    build_plant_lookup_from_db,
    build_locked_placements,
    candidate_conflicts_with_locked,
    create_instance_payload_local,
    master_position_to_local,
)


IMPOSSIBLE = -10**6


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def cell_to_list(cell):
    if cell == "" or cell is None:
        return []
    if isinstance(cell, list):
        return cell[:]
    return [cell]


def insertion_sort_by_size(items):
    for i in range(1, len(items)):
        key_item = items[i]
        key_size = key_item[0]["size"]
        key_amount = key_item[1]

        j = i - 1
        while (
            j >= 0
            and (
                items[j][0]["size"] < key_size
                or (items[j][0]["size"] == key_size and items[j][1] > key_amount)
            )
        ):
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key_item

    return items


def sorting_list_relationship(lst):
    rel1 = []
    rel2 = []
    rel0 = []
    relN = []
    new_list = []

    names_in_list = [x[0]["name"] for x in lst]

    for item in lst:
        helps = item[0]["helps"]
        helps_by = item[0]["helps_by"]

        has_1way = False
        has_2way = False

        for name in names_in_list:
            in_helps = name in helps
            in_helps_by = name in helps_by

            if in_helps or in_helps_by:
                has_1way = True
            if in_helps and in_helps_by:
                has_2way = True

        if has_2way:
            rel2.append(item)
        elif has_1way:
            rel1.append(item)
        else:
            rel0.append(item)

    rel2 = insertion_sort_by_size(rel2)
    rel1 = insertion_sort_by_size(rel1)
    rel0 = insertion_sort_by_size(rel0)
    relN = insertion_sort_by_size(relN)

    return rel2 + rel1 + rel0 + relN


def expand_items(lst):
    expanded = []
    previous_counts = {}

    for plant, amount in lst:
        name = plant["name"]
        already_seen = previous_counts.get(name, 0)

        for i in range(amount):
            # is_same is based on real plant name, not the max-spread group.
            expanded.append([plant, already_seen + i > 0])

        previous_counts[name] = already_seen + amount

    return expanded


def has_avoid_relationship(placing_name, existing_name, placing_plant, plants):
    """
    Hard avoid rule, checked both ways.
    This catches carrot->dill and dill->carrot regardless of placement order.
    """
    if placing_name == existing_name:
        return False

    placing_avoid = placing_plant.get("avoid", [])
    existing_plant = plants.get(existing_name) if plants else None
    existing_avoid = existing_plant.get("avoid", []) if existing_plant else []

    return existing_name in placing_avoid or placing_name in existing_avoid


def relation_score(placing_name, existing_name, placing_plant, plants=None):
    if placing_name == existing_name:
        return IMPOSSIBLE

    if has_avoid_relationship(placing_name, existing_name, placing_plant, plants or {}):
        return -1000

    helps = placing_plant.get("helps", [])
    helps_by = placing_plant.get("helps_by", [])

    a_to_b = existing_name in helps
    b_to_a = existing_name in helps_by

    if a_to_b and b_to_a:
        return 2
    if a_to_b or b_to_a:
        return 1
    return 0

def can_overlap_with(cell, placing_plant, plants, allow_same_overlap=True, no_companion_overlap=False):
    """
    Hard candidate validity check.
    Avoid plants can never overlap, even if max spread/halo fallback is relaxed.
    """
    existing = cell_to_list(cell)
    if not existing:
        return True

    if len(existing) >= 2:
        return False

    placing_name = placing_plant["name"]

    for existing_name in existing:
        if existing_name == placing_name:
            return bool(allow_same_overlap)

        if no_companion_overlap:
            return False

        if has_avoid_relationship(placing_name, existing_name, placing_plant, plants):
            return False

        if relation_score(placing_name, existing_name, placing_plant, plants) <= 0:
            return False

    return True

def has_plant(cell, name):
    return name in cell_to_list(cell)


def locked_cells_for_name(locked, placing_name):
    cells = set()
    for locked_item in locked or []:
        if locked_item["name"] == placing_name:
            cells.update(locked_item.get("same_cells", locked_item["actual_cells"]))
    return cells


def exact_side_pattern_bonus(grid, x, y, size, placing_name, locked=None, force_row=False, force_column=False):
    rows = len(grid)
    cols = len(grid[0])
    locked_cells = locked_cells_for_name(locked, placing_name)

    def cell_has_name(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        return has_plant(grid[r][c], placing_name) or (r, c) in locked_cells

    top_full = all(cell_has_name(x - 1, y + i) for i in range(size)) if x - 1 >= 0 else False
    bottom_full = all(cell_has_name(x + size, y + i) for i in range(size)) if x + size < rows else False
    left_full = all(cell_has_name(x + i, y - 1) for i in range(size)) if y - 1 >= 0 else False
    right_full = all(cell_has_name(x + i, y + size) for i in range(size)) if y + size < cols else False

    vertical_edges = int(top_full) + int(bottom_full)
    horizontal_edges = int(left_full) + int(right_full)
    total_edges = vertical_edges + horizontal_edges

    if not force_row and not force_column:
        return 0

    preferred_edges = horizontal_edges if force_row else vertical_edges
    wrong_edges = vertical_edges if force_row else horizontal_edges

    bonus = preferred_edges * max(18, size * 10)
    bonus -= wrong_edges * max(18, size * 10)

    if preferred_edges > 0 and wrong_edges == 0:
        bonus += max(12, size * 6)

    if preferred_edges == 2 and wrong_edges == 0:
        bonus += max(8, size * 4)

    if total_edges == 0:
        return 0

    return bonus


def compact_clump_bonus(grid, x, y, size, placing_name, locked=None):
    """
    Square-ish clumping bonus.
    It rewards a compact bounding box and punishes empty holes / long thin shapes.
    This is only used when force row/column is off.
    """
    rows = len(grid)
    cols = len(grid[0])
    existing_cells = set(locked_cells_for_name(locked, placing_name))

    for r in range(rows):
        for c in range(cols):
            if has_plant(grid[r][c], placing_name):
                existing_cells.add((r, c))

    if not existing_cells:
        return 0

    candidate_cells = {(x + ix, y + iy) for ix in range(size) for iy in range(size)}
    combined = existing_cells | candidate_cells

    min_r = min(r for r, _ in combined)
    max_r = max(r for r, _ in combined)
    min_c = min(c for _, c in combined)
    max_c = max(c for _, c in combined)

    height = max_r - min_r + 1
    width = max_c - min_c + 1
    area = height * width
    filled = len(combined)
    empty = area - filled

    bonus = 0
    bonus += filled * max(2, size)
    bonus -= empty * max(4, size * 2)
    bonus -= abs(height - width) * max(3, size)

    if height == width:
        bonus += max(6, size * 3)

    return bonus


def avoid_penalty(grid, x, y, size, placing_plant, plants):
    penalty = 0
    rows = len(grid)
    cols = len(grid[0])
    placing_name = placing_plant["name"]

    inner_low_r = x
    inner_high_r = x + size - 1
    inner_low_c = y
    inner_high_c = y + size - 1

    # Immediate halo: preferred [avoid][space][plant] behaviour.
    for r in range(x - 1, x + size + 1):
        for c in range(y - 1, y + size + 1):
            if r < 0 or r >= rows or c < 0 or c >= cols:
                continue
            if inner_low_r <= r <= inner_high_r and inner_low_c <= c <= inner_high_c:
                continue

            for plant_name in cell_to_list(grid[r][c]):
                if has_avoid_relationship(placing_name, plant_name, placing_plant, plants):
                    penalty -= 6

    # Softer second halo so it prefers even more distance when possible.
    for r in range(x - 2, x + size + 2):
        for c in range(y - 2, y + size + 2):
            if r < 0 or r >= rows or c < 0 or c >= cols:
                continue

            in_inner = inner_low_r <= r <= inner_high_r and inner_low_c <= c <= inner_high_c
            in_first_halo = x - 1 <= r <= x + size and y - 1 <= c <= y + size
            if in_inner or in_first_halo:
                continue

            for plant_name in cell_to_list(grid[r][c]):
                if has_avoid_relationship(placing_name, plant_name, placing_plant, plants):
                    penalty -= 2

    return penalty


def has_avoid_halo_conflict(grid, x, y, size, placing_plant, plants):
    """
    Soft avoid-spacing rule. When enabled, this blocks candidates whose
    immediate one-cell halo touches an avoid plant. If no candidates exist,
    the search retries with this relaxed.
    """
    rows = len(grid)
    cols = len(grid[0])
    placing_name = placing_plant["name"]

    for r in range(x - 1, x + size + 1):
        for c in range(y - 1, y + size + 1):
            if r < 0 or r >= rows or c < 0 or c >= cols:
                continue
            if x <= r < x + size and y <= c < y + size:
                continue

            for existing_name in cell_to_list(grid[r][c]):
                if has_avoid_relationship(placing_name, existing_name, placing_plant, plants):
                    return True

    return False

def side_adds(grid, x, y, size, placing_name, locked=None, force_row=False, force_column=False):
    num = 0
    rows = len(grid)
    cols = len(grid[0])
    locked_cells = locked_cells_for_name(locked, placing_name)

    def side_weight(is_horizontal):
        if force_row:
            return 2 if is_horizontal else 0
        if force_column:
            return 2 if not is_horizontal else 0
        return 1

    def cell_has_name(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        return has_plant(grid[r][c], placing_name) or (r, c) in locked_cells

    for i in range(size):
        if x - 1 >= 0 and y + i < cols and cell_has_name(x - 1, y + i):
            num += side_weight(False)
        if x + size < rows and y + i < cols and cell_has_name(x + size, y + i):
            num += side_weight(False)
        if y - 1 >= 0 and x + i < rows and cell_has_name(x + i, y - 1):
            num += side_weight(True)
        if y + size < cols and x + i < rows and cell_has_name(x + i, y + size):
            num += side_weight(True)

    return num


def compact_fill_score(grid):
    """
    Extra scoring used when max-spread/fill mode is on.

    It rewards occupied usable cells but penalises holes inside the occupied
    bounding area. This makes score comparisons prefer layouts that use the
    bed cleanly rather than leaving random empty squares between placed plants.
    """
    rows = len(grid)
    cols = len(grid[0])
    occupied = []

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] is None:
                continue
            if cell_to_list(grid[r][c]):
                occupied.append((r, c))

    if not occupied:
        return 0

    occupied_set = set(occupied)
    min_r = min(r for r, _ in occupied)
    max_r = max(r for r, _ in occupied)
    min_c = min(c for _, c in occupied)
    max_c = max(c for _, c in occupied)

    holes = 0
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if grid[r][c] is None:
                continue
            if (r, c) not in occupied_set:
                holes += 1

    occupied_count = len(occupied_set)
    return occupied_count * 3 - holes * 2


def plant_a_helps_b(plants, a_name, b_name):
    a = plants[a_name]
    b = plants[b_name]
    return b_name in a.get("helps", []) or a_name in b.get("helps_by", [])


def pair_relation_score(plants, a_name, b_name):
    if a_name == b_name:
        return 0
    if b_name in plants[a_name].get("avoid", []) or a_name in plants[b_name].get("avoid", []):
        return -1000
    a_to_b = plant_a_helps_b(plants, a_name, b_name)
    b_to_a = plant_a_helps_b(plants, b_name, a_name)
    if a_to_b and b_to_a:
        return 2
    if a_to_b or b_to_a:
        return 1
    return 0


def total_score_grid(plants, grid, avoid, next_to, fill=False, force_row=False, force_column=False):
    score = 0
    rows = len(grid)
    cols = len(grid[0])

    def neighbour_same_bonus(is_horizontal):
        if force_row:
            return 2 if is_horizontal else 0
        if force_column:
            return 2 if not is_horizontal else 0
        return 1

    for i in range(rows):
        for j in range(cols):
            if grid[i][j] is None:
                continue

            cell = cell_to_list(grid[i][j])

            if fill and len(cell) > 0:
                score += 1

            if len(cell) == 2:
                plant1_name = cell[0]
                plant2_name = cell[1]
                plant1 = plants[plant1_name]
                plant2 = plants[plant2_name]

                if has_avoid_relationship(plant1_name, plant2_name, plant1, plants):
                    score -= 1000

                rel = pair_relation_score(plants, plant1_name, plant2_name)
                if rel > 0:
                    score += rel

            neighbour_specs = []
            if i + 1 < rows and grid[i + 1][j] is not None:
                neighbour_specs.append((cell_to_list(grid[i + 1][j]), False))
            if j + 1 < cols and grid[i][j + 1] is not None:
                neighbour_specs.append((cell_to_list(grid[i][j + 1]), True))

            for plant_name in cell:
                plant = plants[plant_name]
                for neighbour_cell, is_horizontal in neighbour_specs:
                    for other_name in neighbour_cell:
                        if next_to and other_name == plant_name:
                            score += neighbour_same_bonus(is_horizontal)
                        if avoid and has_avoid_relationship(plant_name, other_name, plant, plants):
                            score -= 4

    if fill:
        score += compact_fill_score(grid)

    return score

def build_combined_grid(box_sizes, gap=1):
    if not box_sizes:
        return [], [], set(), []

    max_rows = max(a for a, b in box_sizes)
    total_cols = sum(b for a, b in box_sizes) + gap * (len(box_sizes) - 1)

    actual_grid = [[None for _ in range(total_cols)] for _ in range(max_rows)]
    num_grid = [[None for _ in range(total_cols)] for _ in range(max_rows)]
    usable_cells = set()
    box_ranges = []

    col_start = 0
    for idx, (a, b) in enumerate(box_sizes):
        box_ranges.append({
            "box_index": idx,
            "rows": a,
            "cols": b,
            "row_start": 0,
            "col_start": col_start,
        })

        for r in range(a):
            for c in range(b):
                actual_grid[r][col_start + c] = ""
                num_grid[r][col_start + c] = -50
                usable_cells.add((r, col_start + c))

        col_start += b + gap

    return actual_grid, num_grid, usable_cells, box_ranges


def split_into_separate_grids(master_grid, box_ranges):
    split_grids = []
    for box in box_ranges:
        small_grid = []
        for r in range(box["row_start"], box["row_start"] + box["rows"]):
            row = []
            for c in range(box["col_start"], box["col_start"] + box["cols"]):
                row.append(master_grid[r][c])
            small_grid.append(row)
        split_grids.append(small_grid)
    return split_grids


def apply_locked_to_grid(actual_grid, same_grid, locked):
    new_actual = [row[:] for row in actual_grid]
    new_same = [row[:] for row in same_grid]

    for locked_item in locked:
        name = locked_item["name"]

        for r, c in locked_item["actual_cells"]:
            existing = cell_to_list(new_actual[r][c])
            if name not in existing:
                existing.append(name)
            new_actual[r][c] = existing[0] if len(existing) == 1 else existing[:2]

        for r, c in locked_item["same_cells"]:
            existing = cell_to_list(new_same[r][c])
            if name not in existing:
                existing.append(name)
            new_same[r][c] = existing[0] if len(existing) == 1 else existing[:2]

    return new_actual, new_same


def remove_name_from_cell(cell, plant_name):
    if cell is None:
        return None

    filtered = [x for x in cell_to_list(cell) if x != plant_name]
    if len(filtered) == 0:
        return ""
    if len(filtered) == 1:
        return filtered[0]
    return filtered[:2]


def build_same_grid_for_name(actual_grid, locked, plant_name):
    same_grid = [[remove_name_from_cell(cell, plant_name) for cell in row] for row in actual_grid]

    for locked_item in locked:
        if locked_item["name"] != plant_name:
            continue

        for r, c in locked_item["same_cells"]:
            existing = cell_to_list(same_grid[r][c])
            if plant_name not in existing:
                existing.append(plant_name)
            same_grid[r][c] = existing[0] if len(existing) == 1 else existing[:2]

    return same_grid


def is_locked_same_name_actual_cell(cell_pos, cell, placing_name, locked):
    existing = cell_to_list(cell)
    if len(existing) != 1 or existing[0] != placing_name:
        return False

    return any(
        locked_item["name"] == placing_name and cell_pos in locked_item["actual_cells"]
        for locked_item in locked
    )


def empty_cell_bonus(grid, x, y, size):
    bonus = 0
    for ix in range(size):
        for iy in range(size):
            if grid[x + ix][y + iy] == "":
                bonus += 1
    return bonus


def box_full_capacity_for_size(box_sizes, size):
    if size <= 0:
        return 0

    capacity = 0
    for rows, cols in box_sizes:
        capacity += (rows // size) * (cols // size)
    return capacity


def split_for_soft_max_spread(adjusted_lists, box_sizes):
    """
    Pre-split max-spread logic.

    Max spread should mean: use full plant size for same-type spacing where
    possible, but relax as few copies as possible back to size_same when the
    bed is too crowded.

    This is intentionally cheap and happens before backtracking. It avoids the
    expensive retry/branch fallback behaviour while still preventing one plant
    type from reserving unrealistic full spacing for every copy.
    """
    total_usable_area = sum(rows * cols for rows, cols in box_sizes)

    groups = []
    for plant, amount in adjusted_lists:
        full_size = max(1, int(plant["size"]))
        same_size = max(1, int(plant["size_same"]))
        isolated_capacity = box_full_capacity_for_size(box_sizes, full_size)

        full_count = min(amount, isolated_capacity)
        relaxed_count = amount - full_count

        groups.append({
            "plant": plant,
            "amount": amount,
            "full_count": full_count,
            "relaxed_count": relaxed_count,
            "full_area": full_size * full_size,
            "relaxed_area": same_size * same_size,
            "saving": max(0, (full_size * full_size) - (same_size * same_size)),
        })

    def estimated_area():
        return sum(
            g["full_count"] * g["full_area"] +
            g["relaxed_count"] * g["relaxed_area"]
            for g in groups
        )

    # Global pressure correction: if the isolated capacities are too optimistic,
    # relax one copy at a time. This squishes as few copies as possible while
    # leaving room for other plant types.
    while estimated_area() > total_usable_area:
        candidates = [g for g in groups if g["full_count"] > 0 and g["saving"] > 0]
        if not candidates:
            break

        # Relax the copy that frees the most space first. Tie-break by the plant
        # currently using the most full-size area.
        target = max(
            candidates,
            key=lambda g: (g["saving"], g["full_count"] * g["full_area"]),
        )
        target["full_count"] -= 1
        target["relaxed_count"] += 1

    result = []
    for g in groups:
        plant = g["plant"]

        if g["full_count"] > 0:
            full_plant = dict(plant)
            full_plant["_strict_same_spacing"] = True
            result.append([full_plant, g["full_count"]])

        if g["relaxed_count"] > 0:
            relaxed_plant = dict(plant)
            relaxed_plant["_strict_same_spacing"] = False
            result.append([relaxed_plant, g["relaxed_count"]])

    return result


def split_for_planned_max_spread(adjusted_lists, box_sizes):
    """
    Medium max-spread planning step.

    Max spread is soft, but the solver should not wait until a plant is deleted
    before it discovers that some copies need to squeeze. This function estimates
    how many copies must use normal same-plant spacing (`size_same`) before the
    search starts.

    It keeps the rule cheap:
    - estimate full-size area needed by all requested plants;
    - compare against total usable box area;
    - relax copies from the most common/most space-saving plant types first;
    - never changes hard rules such as avoid overlap or max 2 plants per cell.
    """
    if not adjusted_lists:
        return []

    total_usable_area = sum(rows * cols for rows, cols in box_sizes)

    groups = []
    for plant, amount in adjusted_lists:
        full_size = max(1, int(plant["size"]))
        same_size = max(1, int(plant["size_same"]))
        full_area = full_size * full_size
        same_area = same_size * same_size
        saving = max(0, full_area - same_area)

        # If this plant type cannot even fit all copies at full spacing in
        # isolation, those extra copies are already known to need squeezing.
        isolated_capacity = box_full_capacity_for_size(box_sizes, full_size)
        relaxed_count = max(0, amount - isolated_capacity)

        groups.append({
            "plant": plant,
            "amount": amount,
            "full_size": full_size,
            "same_size": same_size,
            "full_area": full_area,
            "same_area": same_area,
            "saving": saving,
            "relaxed_count": min(amount, relaxed_count),
        })

    def estimated_area():
        total = 0
        for g in groups:
            strict_count = g["amount"] - g["relaxed_count"]
            total += strict_count * g["full_area"]
            total += g["relaxed_count"] * g["same_area"]
        return total

    over_cells = max(0, estimated_area() - total_usable_area)

    # Relax enough copies to cover the estimated over-capacity.
    # This follows the idea of converting an area overflow into an approximate
    # one-direction squeeze requirement, then dividing by how much each squeezed
    # copy can shrink in that direction.
    while over_cells > 0:
        candidates = [
            g for g in groups
            if g["relaxed_count"] < g["amount"] and g["saving"] > 0
        ]
        if not candidates:
            break

        target = max(
            candidates,
            key=lambda g: (
                g["amount"] - g["relaxed_count"],  # most common remaining strict plant
                g["saving"],
                g["full_size"],
            ),
        )

        direction_cells_needed = max(1, math.ceil(over_cells / target["full_size"]))
        squeeze_per_copy = max(1, target["full_size"] - target["same_size"])
        copies_needed = math.ceil(direction_cells_needed / squeeze_per_copy) + 1

        remaining_strict = target["amount"] - target["relaxed_count"]
        copies_to_relax = max(1, min(remaining_strict, copies_needed))

        target["relaxed_count"] += copies_to_relax
        over_cells = max(0, estimated_area() - total_usable_area)

    result = []
    for g in groups:
        plant = g["plant"]
        relaxed_count = g["relaxed_count"]
        strict_count = g["amount"] - relaxed_count

        # Put planned squeezed copies first so they create a compact same-type
        # cluster before full-spread copies reserve too much room.
        if relaxed_count > 0:
            relaxed_plant = dict(plant)
            relaxed_plant["_force_relaxed_same_spacing"] = True
            relaxed_plant["_strict_same_spacing"] = False
            result.append([relaxed_plant, relaxed_count])

        if strict_count > 0:
            strict_plant = dict(plant)
            strict_plant["_force_relaxed_same_spacing"] = False
            strict_plant["_strict_same_spacing"] = True
            result.append([strict_plant, strict_count])

    return result


def get_candidates(
    actual,
    same,
    is_same,
    usable_cells,
    num,
    item,
    next_to,
    avoid,
    fill,
    plants,
    locked,
    force_row=False,
    force_column=False,
    strict_same_separation=False,
    strict_avoid_halo=False,
    no_companion_overlap=False,
):
    rows = len(actual)
    cols = len(actual[0])
    plant = item[0]
    size = plant["size"]
    size_same = plant["size_same"]
    placing_name = plant["name"]

    grid_to_use = actual if strict_same_separation else (same if is_same else actual)

    def score_cell(x, y, cell):
        existing = cell_to_list(cell)
        if not existing:
            return 0

        if placing_name in existing:
            if is_locked_same_name_actual_cell((x, y), cell, placing_name, locked):
                return 0
            return IMPOSSIBLE

        if len(existing) >= 2:
            return IMPOSSIBLE

        s = 0
        for existing_name in existing:
            rel = relation_score(placing_name, existing_name, plant, plants)
            # Companion overlap should beat empty-space/fill bonuses. Avoid remains huge negative.
            s += rel * 20 if rel > 0 else rel
        return s

    for x in range(rows):
        for y in range(cols):
            if (x, y) not in usable_cells:
                num[x][y] = IMPOSSIBLE
                continue

            num[x][y] = score_cell(x, y, grid_to_use[x][y])

    legal = []

    for x in range(rows - size + 1):
        for y in range(cols - size + 1):
            ok = True

            for ix in range(size):
                for iy in range(size):
                    cell_pos = (x + ix, y + iy)
                    if cell_pos not in usable_cells:
                        ok = False
                        break

                    cell = grid_to_use[x + ix][y + iy]

                    # Same-name cells in grid_to_use represent the same-plant spacing/core
                    # area, not just the visual footprint. Squished max-spread means
                    # use size_same spacing, not exact same-cell stacking.
                    if placing_name in cell_to_list(cell):
                        ok = False
                        break
                    if not can_overlap_with(cell, plant, plants, allow_same_overlap=not strict_same_separation, no_companion_overlap=no_companion_overlap):
                        ok = False
                        break

            if not ok:
                continue

            candidate = {
                "x": x,
                "y": y,
                "actual_cells": [(x + ix, y + iy) for ix in range(size) for iy in range(size)],
                "same_cells": [(x + ix, y + iy) for ix in range(size_same) for iy in range(size_same)],
            }

            if strict_avoid_halo and has_avoid_halo_conflict(actual, x, y, size, plant, plants):
                continue

            if candidate_conflicts_with_locked(plants, candidate, placing_name, locked):
                continue

            s = 0
            for ix in range(size):
                for iy in range(size):
                    s += num[x + ix][y + iy]

            if next_to:
                # Same-plant closeness is based on size_same/core cells, not the full spacing footprint.
                s += side_adds(
                    same,
                    x,
                    y,
                    size_same,
                    placing_name,
                    locked,
                    force_row=force_row,
                    force_column=force_column,
                ) * 20

            if fill:
                s += empty_cell_bonus(actual, x, y, size)

            if avoid:
                s += avoid_penalty(actual, x, y, size, plant, plants)

            if next_to and (force_row or force_column):
                s += exact_side_pattern_bonus(
                    same,
                    x,
                    y,
                    size_same,
                    placing_name,
                    locked,
                    force_row=force_row,
                    force_column=force_column,
                )

            if next_to and not force_row and not force_column:
                s += compact_clump_bonus(same, x, y, size_same, placing_name, locked)

            legal.append([x, y, s])

    return legal



def get_candidates_with_soft_fallback(
    actual_grid,
    same_grid,
    effective_is_same,
    usable_cells,
    plant,
    next_to,
    avoid,
    fill,
    plants,
    locked,
    force_row,
    force_column,
    prefer_strict_same,
    no_companion_overlap=False,
):
    """
    Mixed soft-rule candidate search.

    Strict max-spread candidates are preferred, but relaxed same-size candidates
    are also kept as backup branches. This lets the solver squish only the
    individual plant copies needed to make later plants fit.

    Hard rules never relax:
    - plant footprint must fit inside usable cells
    - max 2 plant types per cell
    - avoid plants cannot overlap
    """
    rows = len(actual_grid)
    cols = len(actual_grid[0])

    same_modes = [False]
    if prefer_strict_same:
        same_modes = [True, False]

    halo_modes = [False]
    if avoid:
        halo_modes = [True, False]

    mode_list = []
    for strict_same in same_modes:
        for strict_halo in halo_modes:
            relaxed_same = int(prefer_strict_same and not strict_same)
            relaxed_halo = int(avoid and not strict_halo)
            soft_cost = relaxed_same * 1000 + relaxed_halo * 100
            mode_list.append((strict_same, strict_halo, relaxed_same, relaxed_halo, soft_cost))

    seen = {}

    for strict_same, strict_halo, relaxed_same, relaxed_halo, soft_cost in mode_list:
        num = [[-50 for _ in range(cols)] for _ in range(rows)]
        cands = get_candidates(
            actual_grid,
            same_grid,
            effective_is_same,
            usable_cells,
            num,
            [plant, 1],
            next_to,
            avoid,
            fill,
            plants,
            locked,
            force_row=force_row,
            force_column=force_column,
            strict_same_separation=strict_same,
            strict_avoid_halo=strict_halo,
            no_companion_overlap=no_companion_overlap,
        )

        for x, y, score in cands:
            adjusted_score = score - soft_cost
            cand = {
                "x": x,
                "y": y,
                "score": adjusted_score,
                "raw_score": score,
                "strict_same": strict_same,
                "strict_halo": strict_halo,
                "relaxed_same": relaxed_same,
                "relaxed_halo": relaxed_halo,
                "soft_cost": soft_cost,
            }

            key = (x, y)
            old = seen.get(key)
            if old is None:
                seen[key] = cand
                continue

            old_rank = (old["soft_cost"], -old["raw_score"])
            new_rank = (cand["soft_cost"], -cand["raw_score"])
            if new_rank < old_rank:
                seen[key] = cand

    all_cands = list(seen.values())
    all_cands.sort(key=lambda c: (c["soft_cost"], -c["score"]))
    return all_cands

def prune_candidates(cands, k=3, score_gap=12):
    if not cands:
        return []

    cands = sorted(cands, key=lambda c: (c["soft_cost"], -c["score"]))

    strict = [c for c in cands if c["relaxed_same"] == 0 and c["relaxed_halo"] == 0]
    relaxed = [c for c in cands if c["relaxed_same"] != 0 or c["relaxed_halo"] != 0]

    kept = []

    if strict:
        best_score = strict[0]["score"]
        kept.extend([c for c in strict if c["score"] >= best_score - score_gap][:k])

    # Keep relaxed alternatives even when strict candidates exist.
    # This is the escape hatch for max spread filling the bed before later avoid plants fit.
    relaxed_limit = max(1, min(2, k))
    kept.extend(relaxed[:relaxed_limit])

    if not kept:
        kept = cands[:k]

    out = []
    seen = set()
    for c in kept:
        key = (c["x"], c["y"], c["strict_same"], c["strict_halo"])
        if key in seen:
            continue
        seen.add(key)
        out.append(c)

    return out[: max(k, relaxed_limit)]

def place_copy(actual_grid, same_grid, plant, x, y, strict_same_separation=False):
    new_actual = [row[:] for row in actual_grid]
    new_same = [row[:] for row in same_grid]

    name = plant["name"]
    size = plant["size"]
    size_same = plant["size"] if strict_same_separation else plant["size_same"]

    for r in range(size):
        for c in range(size):
            actual_existing = cell_to_list(new_actual[x + r][y + c])
            if name not in actual_existing:
                actual_existing.append(name)
            new_actual[x + r][y + c] = actual_existing[0] if len(actual_existing) == 1 else actual_existing[:2]

            if r < size_same and c < size_same:
                same_existing = cell_to_list(new_same[x + r][y + c])
                if name not in same_existing:
                    same_existing.append(name)
                new_same[x + r][y + c] = same_existing[0] if len(same_existing) == 1 else same_existing[:2]

    return new_actual, new_same


def save_best_result(
    plants,
    actual_grid,
    same_grid,
    avoid,
    next_to,
    fill,
    force_row,
    force_column,
    best_result,
    placed_count,
    placed_instances,
    relaxed_same_count=0,
    relaxed_halo_count=0,
    skipped_names=None,
):
    score = total_score_grid(plants, actual_grid, avoid, next_to, fill, force_row, force_column)
    skipped_names = skipped_names or []

    current_rank = (
        placed_count,
        -relaxed_same_count,
        -relaxed_halo_count,
        score,
    )
    best_rank = (
        best_result["placed"],
        -best_result.get("relaxed_same_count", 10**9),
        -best_result.get("relaxed_halo_count", 10**9),
        best_result["score"],
    )

    if current_rank > best_rank:
        best_result["placed"] = placed_count
        best_result["score"] = score
        best_result["relaxed_same_count"] = relaxed_same_count
        best_result["relaxed_halo_count"] = relaxed_halo_count
        best_result["grid"] = [row[:] for row in actual_grid]
        best_result["same"] = [row[:] for row in same_grid]
        best_result["instances"] = best_result["locked_instances"] + [dict(i) for i in placed_instances]
        best_result["not_placed"] = skipped_names[:]

def search_best(
    plants,
    actual_grid,
    same_grid,
    usable_cells,
    remaining_plants,
    next_to,
    avoid,
    fill,
    force_row,
    force_column,
    prefer_strict_same,
    best_result,
    total_count,
    box_ranges,
    placed_instances=None,
    k=3,
    prev_name=None,
    relaxed_same_count=0,
    relaxed_halo_count=0,
    skipped_names=None,
    no_companion_overlap=False,
):
    if placed_instances is None:
        placed_instances = []
    if skipped_names is None:
        skipped_names = []

    placed_count = len(best_result["locked_instances"]) + len(placed_instances)

    if placed_count + len(remaining_plants) < best_result["placed"]:
        return

    if not remaining_plants:
        save_best_result(
            plants,
            actual_grid,
            same_grid,
            avoid,
            next_to,
            fill,
            force_row,
            force_column,
            best_result,
            placed_count,
            placed_instances,
            relaxed_same_count,
            relaxed_halo_count,
            skipped_names,
        )
        return

    plant, is_same = remaining_plants[0]
    current_name = plant["name"]

    if prev_name is None or current_name != prev_name:
        same_grid = build_same_grid_for_name(actual_grid, best_result["locked"], current_name)

    has_locked_same = any(locked_item["name"] == current_name for locked_item in best_result["locked"])
    effective_is_same = is_same or has_locked_same

    # Dynamic max-spread behaviour for medium:
    # when fill/max-spread is on, strict full-size same-type spacing is preferred,
    # but relaxed size_same candidates are kept as backup branches with a penalty.
    # This lets backtracking squish only the copies needed to fit later plants.
    raw_cands = get_candidates_with_soft_fallback(
        actual_grid,
        same_grid,
        effective_is_same,
        usable_cells,
        plant,
        next_to,
        avoid,
        fill,
        plants,
        best_result["locked"],
        force_row,
        force_column,
        prefer_strict_same=bool(fill) and not plant.get("_force_relaxed_same_spacing", False),
        no_companion_overlap=no_companion_overlap,
    )

    cands = prune_candidates(
        raw_cands,
        k=k,
        score_gap=18 if fill else 12,
    )

    for cand in cands:
        x = cand["x"]
        y = cand["y"]
        used_strict_same = cand["strict_same"]

        local = master_position_to_local(box_ranges, x, y)
        placed_instance = create_instance_payload_local(
            name=plant["name"],
            box_index=local["box_index"],
            row=local["row"],
            col=local["col"],
            size=plant["size"],
            size_same=plant["size"] if used_strict_same else plant["size_same"],
            locked=False,
        )

        new_actual, new_same = place_copy(
            actual_grid,
            same_grid,
            plant,
            x,
            y,
            strict_same_separation=used_strict_same,
        )

        search_best(
            plants,
            new_actual,
            new_same,
            usable_cells,
            remaining_plants[1:],
            next_to,
            avoid,
            fill,
            force_row,
            force_column,
            prefer_strict_same,
            best_result,
            total_count,
            box_ranges,
            placed_instances + [placed_instance],
            k=k,
            prev_name=current_name,
            relaxed_same_count=relaxed_same_count + cand["relaxed_same"],
            relaxed_halo_count=relaxed_halo_count + cand["relaxed_halo"],
            skipped_names=skipped_names,
            no_companion_overlap=no_companion_overlap,
        )

    # Optional skip branch: if a plant genuinely cannot fit without breaking hard
    # rules, leave that one unplaced and continue with later plants.
    if placed_count + len(remaining_plants) - 1 >= best_result["placed"]:
        search_best(
            plants,
            actual_grid,
            same_grid,
            usable_cells,
            remaining_plants[1:],
            next_to,
            avoid,
            fill,
            force_row,
            force_column,
            prefer_strict_same,
            best_result,
            total_count,
            box_ranges,
            placed_instances,
            k=k,
            prev_name=current_name,
            relaxed_same_count=relaxed_same_count,
            relaxed_halo_count=relaxed_halo_count,
            skipped_names=skipped_names + [current_name],
            no_companion_overlap=no_companion_overlap,
        )

def placing_with_backtracking(
    plants,
    box_sizes,
    lists,
    locked_plants,
    next_to,
    avoid,
    fill=False,
    force_row=False,
    force_column=False,
    k=3,
    no_companion_overlap=False,
):
    actual_grid, grid_num, usable_cells, box_ranges = build_combined_grid(box_sizes)

    same_grid = [row[:] for row in actual_grid]
    locked, locked_count_by_name, locked_instances = build_locked_placements(plants, locked_plants, box_ranges)
    actual_grid, same_grid = apply_locked_to_grid(actual_grid, same_grid, locked)

    adjusted_lists = []
    requested_count_by_name = {}

    for plant_data, amount in lists:
        requested_count_by_name[plant_data["name"]] = amount

    for plant_data, amount in lists:
        locked_count = locked_count_by_name.get(plant_data["name"], 0)
        if locked_count > amount:
            raise ValueError(f"Locked count for '{plant_data['name']}' is greater than requested amount")

        remaining = amount - locked_count
        if remaining > 0:
            adjusted_lists.append([plant_data, remaining])

    for locked_name in locked_count_by_name:
        if locked_name not in requested_count_by_name:
            raise ValueError(f"Locked plant '{locked_name}' was not included in the selected plant amounts")

    # In this project max spread is represented by fill=True for the medium solver.
    # Plan the minimum likely number of squeezed same-type copies first, then let
    # backtracking place them. This prevents early full-spread copies from using
    # all available space and causing later plants to be dropped.
    if fill:
        adjusted_lists = split_for_planned_max_spread(adjusted_lists, box_sizes)

    prefer_strict_same = bool(fill)

    expanded = expand_items(adjusted_lists)

    best_result = {
        "score": -10**18,
        "grid": None,
        "same": None,
        "placed": -1,
        "instances": locked_instances[:],
        "locked_instances": locked_instances[:],
        "locked": locked,
        "relaxed_same_count": 10**9,
        "relaxed_halo_count": 10**9,
        "not_placed": [],
    }

    search_best(
        plants,
        actual_grid,
        same_grid,
        usable_cells,
        expanded,
        next_to,
        avoid,
        fill,
        force_row,
        force_column,
        prefer_strict_same,
        best_result,
        len(expanded),
        box_ranges,
        placed_instances=[],
        k=k,
        no_companion_overlap=no_companion_overlap,
    )

    if best_result["grid"] is None:
        return {
            "result": "No complete solution found",
            "actual_grids": [],
            "same_grids_by_type": {},
            "plant_instances": [],
            "total_score": 0,
            "not_placed": [],
        }

    split_actual_grids = split_into_separate_grids(best_result["grid"], box_ranges)

    same_grids_by_type = {}
    plant_names = sorted(set(item[0]["name"] for item in lists) | set(item["name"] for item in locked))

    for plant_name in plant_names:
        temp_same_grid = [[best_result["grid"][r][c] for c in range(len(best_result["grid"][0]))] for r in range(len(best_result["grid"]))]

        for r in range(len(best_result["same"])):
            for c in range(len(best_result["same"][0])):
                same_cell = cell_to_list(best_result["same"][r][c])
                if plant_name in same_cell:
                    temp_same_grid[r][c] = best_result["same"][r][c]

        same_grids_by_type[plant_name] = split_into_separate_grids(temp_same_grid, box_ranges)

    placed = best_result["placed"]
    total = len(locked_instances) + len(expanded)
    not_placed = best_result.get("not_placed", [])

    # If the best branch ended early for any reason, fill in any missing count
    # with the remaining requested names as a fallback.
    missing_count = max(0, total - placed - len(not_placed))
    if missing_count > 0:
        requested_names = []
        for plant, amount in lists:
            requested_names.extend([plant["name"]] * amount)

        already_placed_names = [item["name"] for item in best_result["instances"]]
        leftovers = requested_names[:]
        for name in already_placed_names:
            if name in leftovers:
                leftovers.remove(name)

        not_placed = not_placed + leftovers[:missing_count]

    return {
        "result": {
            "placed": placed,
            "total": total,
            "score": best_result["score"],
            "status": "FEASIBLE",
            "locked_placed": len(locked_instances),
        },
        "actual_grids": split_actual_grids,
        "same_grids_by_type": same_grids_by_type,
        "plant_instances": best_result["instances"],
        "total_score": total_score_grid(plants, best_result["grid"], avoid, next_to, fill, force_row, force_column),
        "not_placed": not_placed,
    }


def run_autosort_backtracking(payload):
    cell_cm = int(payload.get("cell_cm", 15))
    next_to = bool(payload.get("next_to", True))
    avoid = bool(payload.get("avoid", True))
    fill = bool(payload.get("fill", False))
    force_row = bool(payload.get("force_row", False))
    force_column = bool(payload.get("force_column", False))
    no_companion_overlap = parse_bool(payload.get("no_companion_overlap", False))
    k = int(payload.get("k", 3))

    if force_row and force_column:
        # Frontend should prevent this, but keep backend safe.
        force_column = False

    boxes = payload.get("boxes", [])
    plants_in = payload.get("plants", [])
    locked_plants = payload.get("locked_plants", [])

    if not boxes:
        raise ValueError("boxes is required")

    if not plants_in and not locked_plants:
        raise ValueError("plants or locked_plants is required")

    box_sizes = []
    for box in boxes:
        rows = int(box["rows"])
        cols = int(box["cols"])
        if rows <= 0 or cols <= 0:
            raise ValueError("box rows and cols must be greater than 0")
        box_sizes.append((rows, cols))

    selected_names = [str(item["name"]).strip() for item in plants_in]
    selected_names += [str(item["name"]).strip() for item in locked_plants]
    selected_names = sorted(set(selected_names))

    plant_lookup = build_plant_lookup_from_db(cell_cm=cell_cm, selected_names=selected_names)

    requested_amounts = {}
    for item in plants_in:
        name = str(item["name"]).strip()
        amount = int(item["amount"])
        if amount < 0:
            raise ValueError("plant amount cannot be negative")
        requested_amounts[name] = requested_amounts.get(name, 0) + amount

    for item in locked_plants:
        name = str(item["name"]).strip()
        requested_amounts[name] = requested_amounts.get(name, 0) + 1

    lists = []
    for name, amount in requested_amounts.items():
        if amount <= 0:
            continue
        if name not in plant_lookup:
            raise ValueError(f"{name} is not in the database")
        lists.append([plant_lookup[name], amount])

    ordered_list = sorting_list_relationship(lists)

    result = placing_with_backtracking(
        plants=plant_lookup,
        box_sizes=box_sizes,
        lists=ordered_list,
        locked_plants=locked_plants,
        next_to=next_to,
        avoid=avoid,
        fill=fill,
        force_row=force_row,
        force_column=force_column,
        k=k,
        no_companion_overlap=no_companion_overlap,
    )

    result["algorithm"] = payload.get("algorithm", "backtracking_k")
    return result
