from .constraint_solver import (
    build_plant_lookup_from_db,
    build_locked_placements,
    candidate_conflicts_with_locked,
    create_instance_payload_local,
    master_position_to_local,
)

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
                or (
                    items[j][0]["size"] == key_size
                    and items[j][1] > key_amount
                )
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

    for item in rel2:
        new_list.append(item)
    for item in rel1:
        new_list.append(item)
    for item in rel0:
        new_list.append(item)
    for item in relN:
        new_list.append(item)

    return new_list


def relation_score(placing_name, existing_name, placing_plant):
    if placing_name == existing_name:
        return -10**6

    helps = placing_plant.get("helps", [])
    helps_by = placing_plant.get("helps_by", [])
    avoid = placing_plant.get("avoid", [])

    if existing_name in avoid:
        return -1000

    a_to_b = existing_name in helps
    b_to_a = existing_name in helps_by

    if a_to_b and b_to_a:
        return 2
    if a_to_b or b_to_a:
        return 1
    return 0


def can_overlap_with(cell, placing_plant, allow_same_overlap=True, plants=None):
    existing = cell_to_list(cell)
    if not existing:
        return True

    if len(existing) >= 2:
        return False

    placing_name = placing_plant["name"]
    avoid = placing_plant.get("avoid", [])

    for existing_name in existing:
        if existing_name == placing_name:
            if allow_same_overlap:
                continue
            return False

        if existing_name in avoid:
            return False

        # Avoid is hard in both directions.
        if plants is not None:
            existing_plant = plants.get(existing_name, {})
            if placing_name in existing_plant.get("avoid", []):
                return False

        sc = relation_score(placing_name, existing_name, placing_plant)
        if sc <= 0:
            return False

    return True


def has_plant(cell, name):
    return name in cell_to_list(cell)


def locked_cells_for_name(locked, placing_name):
    cells = set()
    if not locked:
        return cells
    for locked_item in locked:
        if locked_item["name"] == placing_name:
            for cell in locked_item.get("same_cells", locked_item["actual_cells"]):
                cells.add(cell)
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
    rows = len(grid)
    cols = len(grid[0])

    existing_cells = set(locked_cells_for_name(locked, placing_name))

    for r in range(rows):
        for c in range(cols):
            if has_plant(grid[r][c], placing_name):
                existing_cells.add((r, c))

    if not existing_cells:
        return 0

    candidate_cells = {
        (x + ix, y + iy)
        for ix in range(size)
        for iy in range(size)
    }
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




def avoid_penalty(grid, x, y, size, placing_plant):
    penalty = 0
    rows = len(grid)
    cols = len(grid[0])

    avoid = placing_plant.get("avoid", [])
    if not avoid:
        return 0

    inner_low_r = x
    inner_high_r = x + size - 1
    inner_low_c = y
    inner_high_c = y + size - 1

    # First halo = immediate extra space.
    for r in range(x - 1, x + size + 1):
        for c in range(y - 1, y + size + 1):
            if r < 0 or r >= rows or c < 0 or c >= cols:
                continue

            if inner_low_r <= r <= inner_high_r and inner_low_c <= c <= inner_high_c:
                continue

            cell = cell_to_list(grid[r][c])
            for plant_name in cell:
                if plant_name in avoid:
                    penalty -= 6

    # Second halo = softer preference for one more square of distance.
    for r in range(x - 2, x + size + 2):
        for c in range(y - 2, y + size + 2):
            if r < 0 or r >= rows or c < 0 or c >= cols:
                continue

            in_inner = inner_low_r <= r <= inner_high_r and inner_low_c <= c <= inner_high_c
            in_first_halo = (
                x - 1 <= r <= x + size and
                y - 1 <= c <= y + size
            )

            if in_inner or in_first_halo:
                continue

            cell = cell_to_list(grid[r][c])
            for plant_name in cell:
                if plant_name in avoid:
                    penalty -= 2

    return penalty



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

                if plant2_name in plant1.get("avoid", []):
                    score -= 1000
                if plant1_name in plant2.get("avoid", []):
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

                        if avoid and other_name in plant.get("avoid", []):
                            score -= 4

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
        box_ranges.append(
            {
                "box_index": idx,
                "rows": a,
                "cols": b,
                "row_start": 0,
                "col_start": col_start,
            }
        )

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
        row_start = box["row_start"]
        col_start = box["col_start"]
        rows = box["rows"]
        cols = box["cols"]

        small_grid = []
        for r in range(row_start, row_start + rows):
            row = []
            for c in range(col_start, col_start + cols):
                row.append(master_grid[r][c])
            small_grid.append(row)

        split_grids.append(small_grid)

    return split_grids


def apply_locked_to_grid(actual_grid, same_grid, locked):
    new_actual = [row[:] for row in actual_grid]
    new_same = [row[:] for row in same_grid]

    for locked_item in locked:
        name = locked_item["name"]

        for (r, c) in locked_item["actual_cells"]:
            existing = cell_to_list(new_actual[r][c])
            if name not in existing:
                existing.append(name)

            if len(existing) == 0:
                new_actual[r][c] = ""
            elif len(existing) == 1:
                new_actual[r][c] = existing[0]
            else:
                new_actual[r][c] = existing[:2]

        for (r, c) in locked_item["same_cells"]:
            existing = cell_to_list(new_same[r][c])
            if name not in existing:
                existing.append(name)

            if len(existing) == 0:
                new_same[r][c] = ""
            elif len(existing) == 1:
                new_same[r][c] = existing[0]
            else:
                new_same[r][c] = existing[:2]

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
    # Start from actual grid, but remove the full footprint of this plant type.
    # Then add back only the same_cells of locked plants of this type.
    same_grid = [
        [remove_name_from_cell(cell, plant_name) for cell in row]
        for row in actual_grid
    ]

    for locked_item in locked:
        if locked_item["name"] != plant_name:
            continue

        for (r, c) in locked_item["same_cells"]:
            existing = cell_to_list(same_grid[r][c])
            if plant_name not in existing:
                existing.append(plant_name)

            if len(existing) == 0:
                same_grid[r][c] = ""
            elif len(existing) == 1:
                same_grid[r][c] = existing[0]
            else:
                same_grid[r][c] = existing[:2]

    return same_grid

def is_locked_same_name_actual_cell(cell_pos, cell, placing_name, locked):
    existing = cell_to_list(cell)

    # only bypass if this cell is occupied by the same plant name
    if placing_name not in existing:
        return False

    return any(
        locked_item["name"] == placing_name and cell_pos in locked_item["actual_cells"]
        for locked_item in locked
    )

def remove_name_from_cell(cell, plant_name):
    if cell is None:
        return None

    filtered = [x for x in cell_to_list(cell) if x != plant_name]

    if len(filtered) == 0:
        return ""
    if len(filtered) == 1:
        return filtered[0]
    return filtered[:2]


def reset_same_grid_for_name(actual_grid, locked, plant_name):
    same_grid = [
        [remove_name_from_cell(cell, plant_name) for cell in row]
        for row in actual_grid
    ]

    for locked_item in locked:
        if locked_item["name"] != plant_name:
            continue

        for (r, c) in locked_item["same_cells"]:
            existing = cell_to_list(same_grid[r][c])
            if plant_name not in existing:
                existing.append(plant_name)

            if len(existing) == 0:
                same_grid[r][c] = ""
            elif len(existing) == 1:
                same_grid[r][c] = existing[0]
            else:
                same_grid[r][c] = existing[:2]

    return same_grid


def is_locked_same_name_actual_cell(cell_pos, cell, placing_name, locked):
    existing = cell_to_list(cell)

    if len(existing) != 1 or existing[0] != placing_name:
        return False

    return any(
        locked_item["name"] == placing_name and cell_pos in locked_item["actual_cells"]
        for locked_item in locked
    )


def best_place(
    actual,
    same,
    is_same,
    usable_cells,
    num,
    item,
    next_to,
    avoid,
    plants,
    locked,
    fill=False,
    force_row=False,
    force_column=False,
    strict_same_separation=False,
    no_companion_overlap=False,
):
    rows = len(actual)
    cols = len(actual[0])

    def empty_cell_bonus(grid, x, y, size):
        bonus = 0
        for ix in range(size):
            for iy in range(size):
                if grid[x + ix][y + iy] == "":
                    bonus += 1
        return bonus

    size = item[0]["size"]
    size_same = item[0]["size_same"]
    placing_plant = item[0]
    placing_name = placing_plant["name"]

    grid_to_use = actual if strict_same_separation else (same if is_same else actual)

    def score_cell(x, y, cell):
        existing = cell_to_list(cell)
        if not existing:
            return 0

        if placing_name in existing:
            if strict_same_separation:
                return -10**6
            if is_locked_same_name_actual_cell((x, y), cell, placing_name, locked):
                return 0
            return -10**6

        if len(existing) >= 2:
            return -10**6

        s = 0
        for existing_name in existing:
            rel = relation_score(placing_name, existing_name, placing_plant)
            # Companion overlap should beat empty-space/fill bonuses. Avoid remains huge negative.
            s += rel * 20 if rel > 0 else rel
        return s

    for x in range(rows):
        for y in range(cols):
            if (x, y) not in usable_cells:
                num[x][y] = -10**6
                continue

            num[x][y] = score_cell(x, y, grid_to_use[x][y])

    best_score = -10**18
    best_x, best_y = None, None

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

                    existing_names = cell_to_list(cell)
                    if no_companion_overlap and any(existing_name != placing_name for existing_name in existing_names):
                        ok = False
                        break

                    if not can_overlap_with(
                        cell,
                        placing_plant,
                        allow_same_overlap=not strict_same_separation,
                        plants=plants,
                    ):
                        if strict_same_separation or not is_locked_same_name_actual_cell(
                            cell_pos,
                            cell,
                            placing_name,
                            locked,
                        ):
                            ok = False
                            break
                if not ok:
                    break

            if not ok:
                continue

            candidate = {
                "x": x,
                "y": y,
                "actual_cells": [(x + ix, y + iy) for ix in range(size) for iy in range(size)],
                "same_cells": [(x + ix, y + iy) for ix in range(size_same) for iy in range(size_same)],
            }

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
                s += avoid_penalty(actual, x, y, size, placing_plant)

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

            if s > best_score:
                best_score = s
                best_x = x
                best_y = y

    return best_x, best_y



def placing_with_simple_logic(plants, box_sizes, lists, locked_plants, next_to, avoid, fill=False, force_row=False, force_column=False, no_companion_overlap=False):
    """
    Quick greedy placer.

    Important max-spread behaviour:
    - fill=True is the existing "max spread" mode from the frontend.
    - Max spread should try to keep same plants separated using full plant size.
    - If that blocks other plants, retry the whole layout from scratch while relaxing
      only a small number of same-plant copies back to size_same logic.
    - Avoid overlap stays hard. Extra avoid spacing remains a score/soft preference.
    """

    def build_adjusted_lists(locked_count_by_name):
        adjusted = []
        requested = {}

        for plant_data, amount in lists:
            requested[plant_data["name"]] = amount

        for plant_data, amount in lists:
            locked_count = locked_count_by_name.get(plant_data["name"], 0)
            if locked_count > amount:
                raise ValueError(
                    f"Locked count for '{plant_data['name']}' is greater than requested amount"
                )

            remaining = amount - locked_count
            if remaining > 0:
                adjusted.append([plant_data, remaining])

        for locked_name in locked_count_by_name:
            if locked_name not in requested:
                raise ValueError(
                    f"Locked plant '{locked_name}' was not included in the selected plant amounts"
                )

        return adjusted, requested

    def names_have_avoid_relationship(name_a, name_b):
        if name_a == name_b:
            return False

        plant_a = plants.get(name_a, {})
        plant_b = plants.get(name_b, {})

        return (
            name_b in plant_a.get("avoid", [])
            or name_a in plant_b.get("avoid", [])
        )

    def make_relax_priority(adjusted_lists, previous_not_placed=None):
        previous_not_placed = set(previous_not_placed or [])

        priority = []
        for plant_data, amount in adjusted_lists:
            name = plant_data["name"]
            if amount <= 1:
                continue

            size = int(plant_data.get("size", 1))
            size_same = int(plant_data.get("size_same", size))
            saved_per_relaxed_copy = max(0, (size * size) - (size_same * size_same))

            avoids_unplaced = any(
                names_have_avoid_relationship(name, failed_name)
                for failed_name in previous_not_placed
            )

            priority.append(
                {
                    "name": name,
                    "amount": amount,
                    "size": size,
                    "size_same": size_same,
                    "saved": saved_per_relaxed_copy,
                    "avoids_unplaced": avoids_unplaced,
                }
            )

        priority.sort(
            key=lambda x: (
                1 if x["avoids_unplaced"] else 0,
                x["amount"],
                x["saved"],
                x["size"],
            ),
            reverse=True,
        )

        return priority

    def add_one_relaxed_copy(relaxed_quota_by_name, adjusted_lists, previous_not_placed=None):
        priority = make_relax_priority(adjusted_lists, previous_not_placed)

        for item in priority:
            name = item["name"]
            amount = item["amount"]

            # Keep at least one copy trying to use full-size separation where possible.
            # This makes max spread stay visible instead of immediately relaxing the
            # whole plant group.
            max_relax_for_name = max(0, amount - 1)

            if relaxed_quota_by_name.get(name, 0) < max_relax_for_name:
                next_quota = dict(relaxed_quota_by_name)
                next_quota[name] = next_quota.get(name, 0) + 1
                return next_quota

        return None

    def attempt_with_relaxation(relaxed_quota_by_name):
        actual_grid, grid_num, usable_cells, box_ranges = build_combined_grid(box_sizes)

        same_grid = [row[:] for row in actual_grid]
        locked, locked_count_by_name, locked_instances = build_locked_placements(
            plants, locked_plants, box_ranges
        )

        actual_grid, same_grid = apply_locked_to_grid(actual_grid, same_grid, locked)

        adjusted_lists, requested_count_by_name = build_adjusted_lists(locked_count_by_name)

        placed_instances = locked_instances[:]
        cant_place = []

        relaxed_used_by_name = {}

        for item in adjusted_lists:
            placing_plant = item[0]
            name = placing_plant["name"]
            size = placing_plant["size"]
            size_same = placing_plant["size_same"]

            same_grid = build_same_grid_for_name(actual_grid, locked, name)

            # If there is already a locked plant of this same type,
            # the first new copy should also use same-grid logic.
            is_same = locked_count_by_name.get(name, 0) > 0

            for _ in range(item[1]):
                relax_quota = relaxed_quota_by_name.get(name, 0)
                relaxed_used = relaxed_used_by_name.get(name, 0)

                # Max spread means "try strict full-size same separation".
                # If this specific plant group has been given a relaxation quota,
                # only that many copies are allowed to use the normal size_same logic.
                should_relax_this_copy = fill and relaxed_used < relax_quota
                strict_this_copy = fill and not should_relax_this_copy

                if should_relax_this_copy:
                    relaxed_used_by_name[name] = relaxed_used + 1

                x, y = best_place(
                    actual_grid,
                    same_grid,
                    is_same,
                    usable_cells,
                    grid_num,
                    item,
                    next_to,
                    avoid,
                    plants,
                    locked,
                    fill,
                    force_row,
                    force_column,
                    strict_this_copy,
                    no_companion_overlap,
                )

                if x is None:
                    cant_place.append(name)
                    break

                local = master_position_to_local(box_ranges, x, y)
                placed_instances.append(
                    create_instance_payload_local(
                        name=name,
                        box_index=local["box_index"],
                        row=local["row"],
                        col=local["col"],
                        size=size,
                        size_same=size_same,
                        locked=False,
                    )
                )

                for r in range(size):
                    for c in range(size):
                        actual_existing = cell_to_list(actual_grid[x + r][y + c])

                        if name not in actual_existing:
                            actual_existing.append(name)

                        if len(actual_existing) == 0:
                            actual_grid[x + r][y + c] = ""
                        elif len(actual_existing) == 1:
                            actual_grid[x + r][y + c] = actual_existing[0]
                        else:
                            actual_grid[x + r][y + c] = actual_existing[:2]

                        if r < size_same and c < size_same:
                            same_existing = cell_to_list(same_grid[x + r][y + c])

                            if name not in same_existing:
                                same_existing.append(name)

                            if len(same_existing) == 0:
                                same_grid[x + r][y + c] = ""
                            elif len(same_existing) == 1:
                                same_grid[x + r][y + c] = same_existing[0]
                            else:
                                same_grid[x + r][y + c] = same_existing[:2]

                is_same = True

        split_actual_grids = split_into_separate_grids(actual_grid, box_ranges)

        same_grids_by_type = {}
        plant_names = sorted(
            set(item[0]["name"] for item in lists) | set(item["name"] for item in locked)
        )

        for plant_name in plant_names:
            temp_same_grid = [
                [None for _ in range(len(actual_grid[0]))]
                for _ in range(len(actual_grid))
            ]

            for r in range(len(actual_grid)):
                for c in range(len(actual_grid[0])):
                    temp_same_grid[r][c] = actual_grid[r][c]

            for r in range(len(same_grid)):
                for c in range(len(same_grid[0])):
                    same_cell = cell_to_list(same_grid[r][c])
                    if plant_name in same_cell:
                        temp_same_grid[r][c] = same_grid[r][c]

            same_grids_by_type[plant_name] = split_into_separate_grids(
                temp_same_grid, box_ranges
            )

        requested_names = []
        for plant, amount in lists:
            requested_names.extend([plant["name"]] * amount)

        score = total_score_grid(plants, actual_grid, avoid, next_to, fill, force_row, force_column)

        # Prefer more placed plants first, then fewer relaxed copies, then score.
        relaxed_total = sum(relaxed_quota_by_name.values())

        result = {
            "result": {
                "placed": len(placed_instances),
                "total": len(requested_names),
                "score": score,
                "status": "FEASIBLE",
                "locked_placed": len(locked_instances),
                "max_spread_relaxed": relaxed_total,
                "max_spread_relaxed_by_name": dict(relaxed_quota_by_name),
            },
            "actual_grids": split_actual_grids,
            "same_grids_by_type": same_grids_by_type,
            "plant_instances": placed_instances,
            "total_score": score,
            "not_placed": cant_place,
        }

        return result, adjusted_lists

    def strict_slots_for_size(size):
        total = 0
        for box_rows, box_cols in box_sizes:
            total += (box_rows // size) * (box_cols // size)
        return total

    def make_initial_relaxed_quota(adjusted_lists):
        """
        Pre-check for max spread.

        Quick should not keep restarting like backtracking. Before placing,
        estimate how many copies of repeated plants can realistically stay in
        full-size max-spread mode, then relax only the overflow copies.

        Example: a 2x6 box and carrot size=2 has only 3 strict 2x2 slots.
        If the user asks for 6 carrots, pre-mark 3 carrots as relaxed so they
        can use size_same spacing, leaving room for other plants such as dill.
        """
        relaxed_quota = {}

        for plant_data, amount in adjusted_lists:
            if amount <= 1:
                continue

            name = plant_data["name"]
            size = max(1, int(plant_data.get("size", 1)))
            size_same = max(1, int(plant_data.get("size_same", size)))

            # If size_same is not smaller, relaxing cannot save space.
            if size_same >= size:
                continue

            strict_slots = strict_slots_for_size(size)

            # Keep as many copies as possible using full plant size, but relax
            # copies that cannot fit as independent full-size blocks.
            needed_relaxed = max(0, amount - strict_slots)

            # Keep at least one full-size copy where possible so max spread is
            # still visible and not immediately turned into normal same-spacing.
            max_relaxed = max(0, amount - 1)
            needed_relaxed = min(needed_relaxed, max_relaxed)

            if needed_relaxed > 0:
                relaxed_quota[name] = needed_relaxed

        return relaxed_quota

        # Normal behaviour when max spread is off.
    if not fill:
        result, _ = attempt_with_relaxation({})
        return result

    # Quick max-spread:
    # keep greedy speed, but allow a tiny bounded retry loop.
    # This is NOT backtracking. It just retries the whole greedy pass with
    # slightly more same-type spacing relaxed each time.
    actual_grid, grid_num, usable_cells, box_ranges = build_combined_grid(box_sizes)
    locked, locked_count_by_name, locked_instances = build_locked_placements(
        plants, locked_plants, box_ranges
    )
    adjusted_lists, _ = build_adjusted_lists(locked_count_by_name)

    relaxed_quota_by_name = make_initial_relaxed_quota(adjusted_lists)

    best_result = None
    previous_not_placed = []

    max_retries = min(
        8,
        sum(max(0, amount - 1) for _, amount in adjusted_lists) + 1
    )

    for _ in range(max_retries):
        result, adjusted_lists = attempt_with_relaxation(relaxed_quota_by_name)

        if (
            best_result is None
            or result["result"]["placed"] > best_result["result"]["placed"]
            or (
                result["result"]["placed"] == best_result["result"]["placed"]
                and result["total_score"] > best_result["total_score"]
            )
        ):
            best_result = result

        previous_not_placed = result.get("not_placed", [])

        if not previous_not_placed:
            return result

        next_quota = add_one_relaxed_copy(
            relaxed_quota_by_name,
            adjusted_lists,
            previous_not_placed,
        )

        if next_quota is None:
            break

        relaxed_quota_by_name = next_quota

    return best_result


def run_autosort_simple(payload):
    cell_cm = int(payload.get("cell_cm", 15))
    next_to = bool(payload.get("next_to", True))
    avoid = bool(payload.get("avoid", True))
    fill = bool(payload.get("fill", False))
    force_row = bool(payload.get("force_row", False))
    force_column = bool(payload.get("force_column", False))
    no_companion_overlap = parse_bool(payload.get("no_companion_overlap", False))

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

    plant_lookup = build_plant_lookup_from_db(
        cell_cm=cell_cm,
        selected_names=selected_names,
    )

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

    result = placing_with_simple_logic(
        plants=plant_lookup,
        box_sizes=box_sizes,
        lists=ordered_list,
        locked_plants=locked_plants,
        next_to=next_to,
        avoid=avoid,
        fill=fill,
        force_row=force_row,
        force_column=force_column,
        no_companion_overlap=no_companion_overlap,
    )

    result["algorithm"] = payload.get("algorithm", "quick")
    return result