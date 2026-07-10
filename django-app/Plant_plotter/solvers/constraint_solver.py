from math import ceil
from ortools.sat.python import cp_model

from ..models import Plant, Companion_helped_bylistItem, Companion_helpslistItem, Plants_avoidlistItem


def build_plant_lookup_from_db(cell_cm, selected_names):
    db_plants = Plant.objects.filter(name__in=selected_names)

    found_names = set(db_plants.values_list("name", flat=True))
    missing = sorted(set(selected_names) - found_names)
    if missing:
        raise ValueError(f"These plants were not found in the database: {missing}")

    helps_map = {}
    helps_by_map = {}
    avoid_map = {}

    for plant_name in selected_names:
        helps_map[plant_name] = list(
            Companion_helpslistItem.objects.filter(plant__name=plant_name)
            .select_related("other_plant")
            .values_list("other_plant__name", flat=True)
        )

        helps_by_map[plant_name] = list(
            Companion_helped_bylistItem.objects.filter(plant__name=plant_name)
            .select_related("other_plant")
            .values_list("other_plant__name", flat=True)
        )

        avoid_map[plant_name] = list(
            Plants_avoidlistItem.objects.filter(plant__name=plant_name)
            .select_related("other_plant")
            .values_list("other_plant__name", flat=True)
        )

    plants = {}

    for p in db_plants:
        size = max(1, ceil((p.spacing_between_rows or 0) / cell_cm))
        size_same = max(1, ceil((p.spacing_in_rows or 0) / cell_cm))

        plants[p.name] = {
            "name": p.name,
            "size": size,
            "size_same": size_same,
            "helps": helps_map[p.name],
            "helps_by": helps_by_map[p.name],
            "avoid": avoid_map[p.name],
        }

    return plants


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

    for i in lst:
        helps = i[0]["helps"]
        helps_by = i[0]["helps_by"]

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
            rel2.append(i)
        elif has_1way:
            rel1.append(i)
        else:
            rel0.append(i)

    rel2 = insertion_sort_by_size(rel2)
    rel1 = insertion_sort_by_size(rel1)
    rel0 = insertion_sort_by_size(rel0)
    relN = insertion_sort_by_size(relN)

    for i in rel2:
        new_list.append(i)
    for i in rel1:
        new_list.append(i)
    for i in rel0:
        new_list.append(i)
    for i in relN:
        new_list.append(i)

    return new_list


def cell_to_list(cell):
    if cell == "" or cell is None:
        return []
    if isinstance(cell, list):
        return cell[:]
    return [cell]


def plant_a_helps_b(plants, a_name, b_name):
    """True only for the direction a -> b.

    The same direction can be stored as b in a.helps, or as
    a in b.helps_by.  a.helps_by means b helps a, not a helps b.
    """
    a = plants[a_name]
    b = plants[b_name]
    return b_name in a.get("helps", []) or a_name in b.get("helps_by", [])


def relation_score(plants, a_name, b_name):
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


def companion_overlap_reward(rel, overlap_cells):
    """Make true two-way companion overlap decisively beat one-way overlap."""
    if rel >= 2:
        return 120 * overlap_cells
    if rel == 1:
        return 25 * overlap_cells
    return 0


def full_companion_cover_bonus(rel, overlap_cells, cells_a, cells_b):
    """Extra reward when a companion fully covers the smaller plant footprint.

    This keeps row/column/near as same-type shape preferences only, while making
    companion overlap remain a priority. Partial companion overlap is still good,
    but full coverage should win whenever it is valid.
    """
    if rel <= 0 or overlap_cells <= 0:
        return 0

    smaller_footprint = min(len(cells_a), len(cells_b))
    if smaller_footprint <= 0:
        return 0

    if overlap_cells >= smaller_footprint:
        if rel >= 2:
            return 700
        return 220

    return 0


def has_companion_relationship_in_lists(plants, expanded, locked):
    names = sorted(set([item["name"] for item in expanded] + [item["name"] for item in locked]))
    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            if relation_score(plants, name_a, name_b) > 0:
                return True
    return False


def can_overlap_types(plants, a_name, b_name, no_companion_overlap=False):
    if a_name == b_name:
        return True
    if no_companion_overlap:
        return False
    return relation_score(plants, a_name, b_name) > 0


def expand_items(lists):
    expanded = []
    for item in lists:
        plant = item[0]
        amount = item[1]
        for copy_idx in range(amount):
            expanded.append(
                {
                    "instance_id": len(expanded),
                    "name": plant["name"],
                    "size": plant["size"],
                    "size_same": plant["size"] if plant.get("_strict_same_spacing") else plant["size_same"],
                    "strict_same": bool(plant.get("_strict_same_spacing", False)),
                    "copy_idx": copy_idx,
                }
            )
    return expanded


def get_actual_cells(x, y, size):
    cells = []
    for dx in range(size):
        for dy in range(size):
            cells.append((x + dx, y + dy))
    return cells


def get_same_cells(x, y, size_same):
    cells = []
    for dx in range(size_same):
        for dy in range(size_same):
            cells.append((x + dx, y + dy))
    return cells


def shared_cell_count(cells_a, cells_b):
    return len(set(cells_a).intersection(set(cells_b)))


def side_contact_count(cells_a, cells_b):
    set_a = set(cells_a)
    set_b = set(cells_b)
    count = 0

    for (r, c) in set_a:
        if (r - 1, c) in set_b and (r - 1, c) not in set_a:
            count += 1
        if (r + 1, c) in set_b and (r + 1, c) not in set_a:
            count += 1
        if (r, c - 1) in set_b and (r, c - 1) not in set_a:
            count += 1
        if (r, c + 1) in set_b and (r, c + 1) not in set_a:
            count += 1

    return count


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


def to_master_cell(box_ranges, box_index, local_row, local_col):
    if box_index < 0 or box_index >= len(box_ranges):
        raise ValueError(f"Invalid box_index {box_index}")

    box = box_ranges[box_index]
    row = box["row_start"] + local_row
    col = box["col_start"] + local_col

    if local_row < 0 or local_row >= box["rows"] or local_col < 0 or local_col >= box["cols"]:
        raise ValueError(
            f"Locked plant position ({local_row}, {local_col}) is outside box {box_index}"
        )

    return (row, col)


def master_position_to_local(box_ranges, x, y):
    for box in box_ranges:
        row_start = box["row_start"]
        col_start = box["col_start"]
        row_end = row_start + box["rows"]
        col_end = col_start + box["cols"]

        if row_start <= x < row_end and col_start <= y < col_end:
            return {
                "box_index": box["box_index"],
                "row": x - row_start,
                "col": y - col_start,
            }

    raise ValueError(f"Master position ({x}, {y}) does not belong to any box")


def create_instance_payload_local(name, box_index, row, col, size, size_same, locked=False):
    seed_row = row + (size_same - 1) / 2
    seed_col = col + (size_same - 1) / 2

    return {
        "name": name,
        "box_index": box_index,
        "row": row,
        "col": col,
        "width": size,
        "height": size,
        "size_same": size_same,
        "seed_row": seed_row,
        "seed_col": seed_col,
        "locked": locked,
    }


def build_locked_placements(plants, locked_plants, box_ranges, no_companion_overlap=False):
    locked = []
    locked_count_by_name = {}
    locked_instances = []

    for idx, item in enumerate(locked_plants):
        name = str(item["name"]).strip()
        if name not in plants:
            raise ValueError(f"Locked plant '{name}' is not in the selected plant list")

        box_index = int(item["box_index"])
        row = int(item["row"])
        col = int(item["col"])

        size = plants[name]["size"]
        size_same = plants[name]["size_same"]

        actual_cells = []
        same_cells = []

        for dr in range(size):
            for dc in range(size):
                actual_cells.append(to_master_cell(box_ranges, box_index, row + dr, col + dc))

        for dr in range(size_same):
            for dc in range(size_same):
                same_cells.append(to_master_cell(box_ranges, box_index, row + dr, col + dc))

        locked.append(
            {
                "id": f"locked_{idx}",
                "name": name,
                "box_index": box_index,
                "row": row,
                "col": col,
                "size": size,
                "size_same": size_same,
                "actual_cells": actual_cells,
                "same_cells": same_cells,
            }
        )

        locked_instances.append(
            create_instance_payload_local(
                name=name,
                box_index=box_index,
                row=row,
                col=col,
                size=size,
                size_same=size_same,
                locked=True,
            )
        )

        locked_count_by_name[name] = locked_count_by_name.get(name, 0) + 1

    for i in range(len(locked)):
        for j in range(i + 1, len(locked)):
            a = locked[i]
            b = locked[j]

            actual_overlap = shared_cell_count(a["actual_cells"], b["actual_cells"])
            if actual_overlap > 0 and not can_overlap_types(plants, a["name"], b["name"], no_companion_overlap=no_companion_overlap):
                raise ValueError(
                    f"Locked plants '{a['name']}' and '{b['name']}' overlap illegally"
                )

            if a["name"] == b["name"]:
                same_overlap = shared_cell_count(a["same_cells"], b["same_cells"])
                if same_overlap > 0:
                    raise ValueError(
                        f"Locked placements for '{a['name']}' overlap inside same-plant spacing"
                    )

    return locked, locked_count_by_name, locked_instances


def candidate_conflicts_with_locked(plants, candidate, plant_name, locked, no_companion_overlap=False):
    for locked_item in locked:
        overlap = shared_cell_count(candidate["actual_cells"], locked_item["actual_cells"])
        if overlap <= 0:
            continue

        if not can_overlap_types(plants, plant_name, locked_item["name"], no_companion_overlap=no_companion_overlap):
            return True

    for locked_item in locked:
        if plant_name != locked_item["name"]:
            continue

        same_overlap = shared_cell_count(candidate["same_cells"], locked_item["same_cells"])
        if same_overlap > 0:
            return True

    return False


def expand_halo_cells(cells, rows, cols):
    halo = set()
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    halo.add((nr, nc))
    return halo


def avoid_halo_conflict(cells_a, cells_b, rows, cols):
    return bool(expand_halo_cells(cells_a, rows, cols) & set(cells_b))


def box_full_capacity_for_size(box_sizes, size):
    if size <= 0:
        return 0
    return sum((rows // size) * (cols // size) for rows, cols in box_sizes)


def split_for_constraint_max_spread(lists, box_sizes):
    """Mark only enough repeated copies as relaxed for CP-SAT max spread.

    Strict copies use full `size` for same-type separation. Relaxed copies use
    normal `size_same`, so max spread stays soft instead of deleting plants.
    """
    total_usable_area = sum(rows * cols for rows, cols in box_sizes)
    groups = []

    for plant, amount in lists:
        full_size = max(1, int(plant["size"]))
        same_size = max(1, int(plant["size_same"]))
        full_area = full_size * full_size
        same_area = same_size * same_size
        saving = max(0, full_area - same_area)
        isolated_capacity = box_full_capacity_for_size(box_sizes, full_size)
        relaxed_count = max(0, amount - isolated_capacity)
        groups.append({
            "plant": plant,
            "amount": amount,
            "full_area": full_area,
            "same_area": same_area,
            "saving": saving,
            "relaxed_count": min(amount, relaxed_count),
        })

    def estimated_area():
        return sum(
            (g["amount"] - g["relaxed_count"]) * g["full_area"]
            + g["relaxed_count"] * g["same_area"]
            for g in groups
        )

    while estimated_area() > total_usable_area:
        candidates = [g for g in groups if g["relaxed_count"] < g["amount"] and g["saving"] > 0]
        if not candidates:
            break
        target = max(candidates, key=lambda g: (g["amount"] - g["relaxed_count"], g["saving"]))
        target["relaxed_count"] += 1

    result = []
    for g in groups:
        relaxed = g["relaxed_count"]
        strict = g["amount"] - relaxed
        if relaxed > 0:
            relaxed_plant = dict(g["plant"])
            relaxed_plant["_strict_same_spacing"] = False
            result.append([relaxed_plant, relaxed])
        if strict > 0:
            strict_plant = dict(g["plant"])
            strict_plant["_strict_same_spacing"] = True
            result.append([strict_plant, strict])
    return result


def build_candidate_positions(rows, cols, expanded, usable_cells, plants, locked, no_companion_overlap=False):
    candidates = {}
    for i, plant in enumerate(expanded):
        candidates[i] = []
        size = plant["size"]
        size_same = plant["size_same"]
        plant_name = plant["name"]

        for x in range(rows - size + 1):
            for y in range(cols - size + 1):
                actual_cells = get_actual_cells(x, y, size)
                same_cells = get_same_cells(x, y, size_same)

                if not all(cell in usable_cells for cell in actual_cells):
                    continue

                candidate = {
                    "x": x,
                    "y": y,
                    "actual_cells": actual_cells,
                    "same_cells": same_cells,
                }

                if candidate_conflicts_with_locked(plants, candidate, plant_name, locked, no_companion_overlap=no_companion_overlap):
                    continue

                candidates[i].append(candidate)

    return candidates


def add_and_var(model, a, b, name):
    both = model.NewBoolVar(name)
    model.Add(both <= a)
    model.Add(both <= b)
    model.Add(both >= a + b - 1)
    return both


def render_solution(rows, cols, expanded, candidates, chosen, usable_cells, locked):
    actual_grid = [[None for _ in range(cols)] for _ in range(rows)]

    for (r, c) in usable_cells:
        actual_grid[r][c] = ""

    for locked_item in locked:
        plant_name = locked_item["name"]
        for (r, c) in locked_item["actual_cells"]:
            existing = cell_to_list(actual_grid[r][c])
            if plant_name not in existing:
                existing.append(plant_name)

            if len(existing) == 0:
                actual_grid[r][c] = ""
            elif len(existing) == 1:
                actual_grid[r][c] = existing[0]
            else:
                actual_grid[r][c] = existing[:2]

    for i, k in chosen.items():
        plant_name = expanded[i]["name"]
        cand = candidates[i][k]

        for (r, c) in cand["actual_cells"]:
            existing = cell_to_list(actual_grid[r][c])
            if plant_name not in existing:
                existing.append(plant_name)

            if len(existing) == 0:
                actual_grid[r][c] = ""
            elif len(existing) == 1:
                actual_grid[r][c] = existing[0]
            else:
                actual_grid[r][c] = existing[:2]

    same_grids_by_type = {}
    plant_names = sorted(set(item["name"] for item in expanded) | set(item["name"] for item in locked))

    for plant_name in plant_names:
        same_grid = [[None for _ in range(cols)] for _ in range(rows)]

        for (r, c) in usable_cells:
            same_grid[r][c] = actual_grid[r][c]

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

        for i, k in chosen.items():
            if expanded[i]["name"] != plant_name:
                continue

            cand = candidates[i][k]

            for (r, c) in cand["same_cells"]:
                existing = cell_to_list(same_grid[r][c])
                if plant_name not in existing:
                    existing.append(plant_name)

                if len(existing) == 0:
                    same_grid[r][c] = ""
                elif len(existing) == 1:
                    same_grid[r][c] = existing[0]
                else:
                    same_grid[r][c] = existing[:2]

        same_grids_by_type[plant_name] = same_grid

    return actual_grid, same_grids_by_type




def full_edge_alignment_count(cells_a, cells_b):
    count = side_contact_count(cells_a, cells_b)
    min_side = max(1, min(len(cells_a), len(cells_b)) ** 0.5)
    try:
        min_side = int(min_side)
    except Exception:
        min_side = 1
    return 1 if count >= min_side else 0


def axis_contact_counts(cells_a, cells_b):
    set_a = set(cells_a)
    set_b = set(cells_b)
    horizontal = 0  # left/right contact, good for row forcing
    vertical = 0    # top/bottom contact, good for column forcing

    for r, c in set_a:
        if (r, c - 1) in set_b or (r, c + 1) in set_b:
            horizontal += 1
        if (r - 1, c) in set_b or (r + 1, c) in set_b:
            vertical += 1

    return horizontal, vertical




def core_center(cells):
    if not cells:
        return (0, 0)
    return (
        sum(r for r, _ in cells) / len(cells),
        sum(c for _, c in cells) / len(cells),
    )


def core_manhattan_distance(cells_a, cells_b):
    ar, ac = core_center(cells_a)
    br, bc = core_center(cells_b)
    return abs(ar - br) + abs(ac - bc)


def same_type_shape_reward(cells_a, cells_b, next_to=False, force_row=False, force_column=False):
    """Score same-type shape using size_same/core cells.

    Plain force-near prefers compact blobs. Row/column modes prefer the chosen
    axis first, while still allowing the next row/column once the first one is
    full instead of treating the second axis as bad.
    """
    if not next_to:
        return 0

    horizontal, vertical = axis_contact_counts(cells_a, cells_b)
    contacts = horizontal + vertical
    distance = core_manhattan_distance(cells_a, cells_b)

    if force_row:
        return int((220 * horizontal) + (45 * vertical) - (18 * distance))

    if force_column:
        return int((220 * vertical) + (45 * horizontal) - (18 * distance))

    # Plain force-near should make a compact blob, not a long line.
    # Pairwise contact alone can still reward a snake/row, so use a much
    # stronger distance penalty across every same-type pair. This keeps nearby
    # touching plants good, but makes far-apart ends of a long row expensive.
    return int((155 * contacts) - (58 * distance))



def add_same_type_global_clump_objective(
    model,
    objective_terms,
    expanded,
    candidates,
    place,
    locked,
    next_to=False,
    force_row=False,
    force_column=False,
):
    """Add a group-level compactness objective for plain force-near.

    Pairwise same-type contact rewards can still make a long snake/row look good
    because each new plant gets a local neighbour. For plain force-near, we also
    score the whole same-type group by its bounding span, so a compact block like
    xxx/xxx beats xxxxxx.

    This deliberately does NOT run for force_row or force_column, because those
    modes have their own directional shape goals.
    """
    if not next_to or force_row or force_column:
        return

    names = sorted(set([item["name"] for item in expanded] + [item["name"] for item in locked]))

    for plant_name in names:
        row_vars = []
        col_vars = []

        for i, item in enumerate(expanded):
            if item["name"] != plant_name:
                continue
            if not candidates.get(i):
                continue

            # Use a doubled centre value so half-cell centres stay integer.
            max_coord = 10**6
            row_expr_terms = []
            col_expr_terms = []

            for k, cand in enumerate(candidates[i]):
                # For plain force-near, compact the displayed/full footprint.
                # Using same_cells here can make the cores look compact while
                # the full plant blocks still appear one space apart.
                shape_cells = cand["actual_cells"]
                if not shape_cells:
                    continue
                row2 = int(round((sum(r for r, _ in shape_cells) * 2) / len(shape_cells)))
                col2 = int(round((sum(c for _, c in shape_cells) * 2) / len(shape_cells)))
                max_coord = max(max_coord if max_coord != 10**6 else 0, row2, col2)
                row_expr_terms.append(row2 * place[(i, k)])
                col_expr_terms.append(col2 * place[(i, k)])

            if not row_expr_terms:
                continue

            row_var = model.NewIntVar(0, max(1, max_coord), f"clump_row_{plant_name}_{i}")
            col_var = model.NewIntVar(0, max(1, max_coord), f"clump_col_{plant_name}_{i}")
            model.Add(row_var == sum(row_expr_terms))
            model.Add(col_var == sum(col_expr_terms))
            row_vars.append(row_var)
            col_vars.append(col_var)

        for locked_item in locked:
            if locked_item["name"] != plant_name:
                continue
            shape_cells = locked_item.get("actual_cells", [])
            if not shape_cells:
                continue
            row2 = int(round((sum(r for r, _ in shape_cells) * 2) / len(shape_cells)))
            col2 = int(round((sum(c for _, c in shape_cells) * 2) / len(shape_cells)))
            row_vars.append(model.NewConstant(row2))
            col_vars.append(model.NewConstant(col2))

        if len(row_vars) < 3:
            continue

        row_min = model.NewIntVar(0, 1000000, f"clump_row_min_{plant_name}")
        row_max = model.NewIntVar(0, 1000000, f"clump_row_max_{plant_name}")
        col_min = model.NewIntVar(0, 1000000, f"clump_col_min_{plant_name}")
        col_max = model.NewIntVar(0, 1000000, f"clump_col_max_{plant_name}")

        model.AddMinEquality(row_min, row_vars)
        model.AddMaxEquality(row_max, row_vars)
        model.AddMinEquality(col_min, col_vars)
        model.AddMaxEquality(col_max, col_vars)

        row_span = model.NewIntVar(0, 1000000, f"clump_row_span_{plant_name}")
        col_span = model.NewIntVar(0, 1000000, f"clump_col_span_{plant_name}")
        model.Add(row_span == row_max - row_min)
        model.Add(col_span == col_max - col_min)

        imbalance = model.NewIntVar(0, 1000000, f"clump_imbalance_{plant_name}")
        model.AddAbsEquality(imbalance, row_span - col_span)

        # Strong enough to beat a long local-contact row, but still below the
        # companion overlap rewards so lettuce can stay fully on carrot.
        objective_terms.append(-220 * (row_span + col_span))
        objective_terms.append(-120 * imbalance)

def partial_same_axis_penalty(cells_a, cells_b):
    contacts = side_contact_count(cells_a, cells_b)
    if contacts <= 0:
        return 0
    return -3 if full_edge_alignment_count(cells_a, cells_b) == 0 else 0

def total_score_grid(plants, grid, avoid, next_to, fill=False, force_row=False, force_column=False):
    score = 0
    rows = len(grid)
    cols = len(grid[0])

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

                rel = relation_score(plants, plant1_name, plant2_name)
                if rel > 0:
                    score += rel

            neighbours = []
            if i + 1 < rows and grid[i + 1][j] is not None:
                neighbours.append(cell_to_list(grid[i + 1][j]))
            if j + 1 < cols and grid[i][j + 1] is not None:
                neighbours.append(cell_to_list(grid[i][j + 1]))

            for plant_name in cell:
                plant = plants[plant_name]

                for neighbour_cell in neighbours:
                    for other_name in neighbour_cell:
                        if next_to and other_name == plant_name:
                            score += 1

                        if avoid and other_name in plant.get("avoid", []):
                            score -= 4

    return score


def build_chosen_instance_payloads(expanded, candidates, chosen, box_ranges):
    instances = []

    for i, k in chosen.items():
        item = expanded[i]
        cand = candidates[i][k]
        local = master_position_to_local(box_ranges, cand["x"], cand["y"])

        instances.append(
            create_instance_payload_local(
                name=item["name"],
                box_index=local["box_index"],
                row=local["row"],
                col=local["col"],
                size=item["size"],
                size_same=item["size_same"],
                locked=False,
            )
        )

    return instances


def placing_with_cp_sat(
    plants,
    box_sizes,
    lists,
    locked_plants=None,
    next_to=True,
    avoid=True,
    fill=False,
    force_row=False,
    force_column=False,
    maximise_search=False,
    time_limit=20,
    _allow_soft_fallback=True,
    no_companion_overlap=False,
):
    if locked_plants is None:
        locked_plants = []

    grid_plants, grid_num, usable_cells, box_ranges = build_combined_grid(box_sizes)

    rows = len(grid_plants)
    cols = len(grid_plants[0])

    locked, locked_count_by_name, locked_instances = build_locked_placements(plants, locked_plants, box_ranges, no_companion_overlap=no_companion_overlap)

    adjusted_lists = []
    requested_count_by_name = {}

    for plant_data, amount in lists:
        requested_count_by_name[plant_data["name"]] = amount

    for plant_data, amount in lists:
        locked_count = locked_count_by_name.get(plant_data["name"], 0)
        if locked_count > amount:
            raise ValueError(
                f"Locked count for '{plant_data['name']}' is greater than requested amount"
            )

        remaining = amount - locked_count
        if remaining > 0:
            adjusted_lists.append([plant_data, remaining])

    for locked_name, locked_count in locked_count_by_name.items():
        if locked_name not in requested_count_by_name:
            raise ValueError(
                f"Locked plant '{locked_name}' was not included in the selected plant amounts"
            )

    if fill:
        adjusted_lists = split_for_constraint_max_spread(adjusted_lists, box_sizes)

    expanded = expand_items(adjusted_lists)
    candidates = build_candidate_positions(rows, cols, expanded, usable_cells, plants, locked, no_companion_overlap=no_companion_overlap)

    model = cp_model.CpModel()

    place = {}
    used = {}

    for i in range(len(expanded)):
        used[i] = model.NewBoolVar(f"used_{i}")

        for k in range(len(candidates[i])):
            place[(i, k)] = model.NewBoolVar(f"place_{i}_{k}")

        model.Add(sum(place[(i, k)] for k in range(len(candidates[i]))) == used[i])

        # Require each requested plant instance to be placed when it has at least
        # one legal candidate. This prevents CP-SAT from returning the trivial
        # "place nothing" result on larger beds when force-near soft scoring is active.
        if len(candidates[i]) > 0:
            model.Add(used[i] == 1)

    # Cell capacity rule: max 2 PLANT TYPES per cell, not max 2 plant instances.
    #
    # This is important for dense same-type planting. For example, several carrot
    # instances may visually cover the same full-spacing cell while still obeying
    # same-plant spacing through the same_cells constraints below. What we must
    # prevent is three different plant types sharing one cell, e.g.
    # carrot + lettuce + dill.
    all_type_names = sorted(set(item["name"] for item in expanded) | set(item["name"] for item in locked))

    for r in range(rows):
        for c in range(cols):
            if (r, c) not in usable_cells:
                continue

            type_occupancy_terms = []

            for plant_name in all_type_names:
                locked_has_type = any(
                    locked_item["name"] == plant_name and (r, c) in locked_item["actual_cells"]
                    for locked_item in locked
                )

                if locked_has_type:
                    # Constants are valid objective/constraint terms in CP-SAT sums.
                    type_occupancy_terms.append(1)
                    continue

                cover_vars_for_type = []
                for i, item in enumerate(expanded):
                    if item["name"] != plant_name:
                        continue

                    for k, cand in enumerate(candidates[i]):
                        if (r, c) in cand["actual_cells"]:
                            cover_vars_for_type.append(place[(i, k)])

                if cover_vars_for_type:
                    type_present = model.NewBoolVar(f"type_{plant_name}_{r}_{c}")
                    model.AddMaxEquality(type_present, cover_vars_for_type)
                    type_occupancy_terms.append(type_present)

            if type_occupancy_terms:
                model.Add(sum(type_occupancy_terms) <= 2)

    plant_name_to_instances = {}
    for i, item in enumerate(expanded):
        plant_name_to_instances.setdefault(item["name"], []).append(i)

    for plant_name, insts in plant_name_to_instances.items():
        for ii in range(len(insts)):
            for jj in range(ii + 1, len(insts)):
                i = insts[ii]
                j = insts[jj]

                for k, cand_i in enumerate(candidates[i]):
                    for l, cand_j in enumerate(candidates[j]):
                        same_overlap = shared_cell_count(
                            cand_i["same_cells"],
                            cand_j["same_cells"]
                        )

                        if same_overlap > 0:
                            model.Add(place[(i, k)] + place[(j, l)] <= 1)

    objective_terms = []

    if fill:
        for r in range(rows):
            for c in range(cols):
                if (r, c) not in usable_cells:
                    continue

                locked_cover_names = set()
                for locked_item in locked:
                    if (r, c) in locked_item["actual_cells"]:
                        locked_cover_names.add(locked_item["name"])

                if locked_cover_names:
                    objective_terms.append(1)
                    continue

                occ = model.NewBoolVar(f"occ_{r}_{c}")
                cover_vars = []
                for i in range(len(expanded)):
                    for k, cand in enumerate(candidates[i]):
                        if (r, c) in cand["actual_cells"]:
                            cover_vars.append(place[(i, k)])

                if cover_vars:
                    model.AddMaxEquality(occ, cover_vars)
                    objective_terms.append(occ)

    BIG_PLACED = 10000

    for _locked_item in locked:
        objective_terms.append(BIG_PLACED)

    for i in range(len(expanded)):
        objective_terms.append(BIG_PLACED * used[i])

    for i in range(len(expanded)):
        name_i = expanded[i]["name"]

        for j in range(i + 1, len(expanded)):
            name_j = expanded[j]["name"]

            for k, cand_i in enumerate(candidates[i]):
                for l, cand_j in enumerate(candidates[j]):
                    actual_overlap_cells = shared_cell_count(
                        cand_i["actual_cells"],
                        cand_j["actual_cells"]
                    )

                    if actual_overlap_cells > 0 and name_i != name_j:
                        if no_companion_overlap or not can_overlap_types(plants, name_i, name_j):
                            model.Add(place[(i, k)] + place[(j, l)] <= 1)
                        else:
                            rel = relation_score(plants, name_i, name_j)
                            if rel > 0:
                                both = add_and_var(
                                    model,
                                    place[(i, k)],
                                    place[(j, l)],
                                    f"ov_{i}_{k}_{j}_{l}",
                                )
                                reward = companion_overlap_reward(rel, actual_overlap_cells)
                                reward += full_companion_cover_bonus(
                                    rel,
                                    actual_overlap_cells,
                                    cand_i["actual_cells"],
                                    cand_j["actual_cells"],
                                )
                                objective_terms.append(reward * both)

                    # Force-near/row/column must only shape SAME plant types.
                    # Different companion types are handled by companion overlap rewards above.
                    if next_to and name_i == name_j:
                        # Same-type grouping is still same-type only.
                        # Plain force-near should visually clump the full plant blocks,
                        # otherwise size_same cores can look compact while the displayed
                        # full footprints leave gaps. Row/column modes keep using the
                        # same-size cores so they still represent plant-to-plant spacing.
                        shape_cells_i = cand_i["same_cells"] if (force_row or force_column) else cand_i["actual_cells"]
                        shape_cells_j = cand_j["same_cells"] if (force_row or force_column) else cand_j["actual_cells"]
                        shape_reward = same_type_shape_reward(
                            shape_cells_i,
                            shape_cells_j,
                            next_to=next_to,
                            force_row=force_row,
                            force_column=force_column,
                        )
                        if shape_reward != 0:
                            both = add_and_var(
                                model,
                                place[(i, k)],
                                place[(j, l)],
                                f"side_{i}_{k}_{j}_{l}",
                            )
                            objective_terms.append(shape_reward * both)

                    if avoid:
                        bad_pair = (
                            name_j in plants[name_i].get("avoid", [])
                            or name_i in plants[name_j].get("avoid", [])
                        )
                        if bad_pair:
                            contacts = side_contact_count(
                                cand_i["actual_cells"],
                                cand_j["actual_cells"]
                            )
                            if contacts > 0:
                                both = add_and_var(
                                    model,
                                    place[(i, k)],
                                    place[(j, l)],
                                    f"avoid_{i}_{k}_{j}_{l}",
                                )
                                objective_terms.append(-4 * contacts * both)

    # Extra-space/avoid toggle: hard one-cell halo for avoid pairs.
    # Avoid overlap is already hard; this adds the requested [avoid][space][plant]
    # behaviour so the solver cannot ignore the toggle for score reasons.
    if avoid:
        for i in range(len(expanded)):
            name_i = expanded[i]["name"]
            for j in range(i + 1, len(expanded)):
                name_j = expanded[j]["name"]
                if relation_score(plants, name_i, name_j) != -1000:
                    continue
                for k, cand_i in enumerate(candidates[i]):
                    for l, cand_j in enumerate(candidates[j]):
                        if avoid_halo_conflict(cand_i["actual_cells"], cand_j["actual_cells"], rows, cols):
                            model.Add(place[(i, k)] + place[(j, l)] <= 1)

    add_same_type_global_clump_objective(
        model,
        objective_terms,
        expanded,
        candidates,
        place,
        locked,
        next_to=next_to,
        force_row=force_row,
        force_column=force_column,
    )

    for locked_item in locked:
        locked_name = locked_item["name"]

        if avoid:
            for i in range(len(expanded)):
                name_i = expanded[i]["name"]
                if relation_score(plants, name_i, locked_name) != -1000:
                    continue
                for k, cand_i in enumerate(candidates[i]):
                    if avoid_halo_conflict(cand_i["actual_cells"], locked_item["actual_cells"], rows, cols):
                        model.Add(place[(i, k)] == 0)

        for i in range(len(expanded)):
            name_i = expanded[i]["name"]

            for k, cand_i in enumerate(candidates[i]):
                actual_overlap_cells = shared_cell_count(
                    cand_i["actual_cells"],
                    locked_item["actual_cells"]
                )

                if actual_overlap_cells > 0 and name_i != locked_name:
                    rel = relation_score(plants, name_i, locked_name)
                    if rel > 0:
                        reward = companion_overlap_reward(rel, actual_overlap_cells)
                        reward += full_companion_cover_bonus(
                            rel,
                            actual_overlap_cells,
                            cand_i["actual_cells"],
                            locked_item["actual_cells"],
                        )
                        objective_terms.append(reward * place[(i, k)])

                # Force-near/row/column must only shape SAME plant types.
                # Different companion types are handled by companion overlap rewards above.
                if next_to and name_i == locked_name:
                    # Same-type grouping against locked plants uses size_same/core cells.
                    shape_reward = same_type_shape_reward(
                        cand_i["same_cells"],
                        locked_item["same_cells"],
                        next_to=next_to,
                        force_row=force_row,
                        force_column=force_column,
                    )
                    if shape_reward != 0:
                        objective_terms.append(shape_reward * place[(i, k)])

                if avoid:
                    bad_pair = (
                        locked_name in plants[name_i].get("avoid", [])
                        or name_i in plants[locked_name].get("avoid", [])
                    )
                    if bad_pair:
                        contacts = side_contact_count(
                            cand_i["actual_cells"],
                            locked_item["actual_cells"]
                        )
                        if contacts > 0:
                            objective_terms.append(-4 * contacts * place[(i, k)])

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8

    has_companion_objective = has_companion_relationship_in_lists(plants, expanded, locked)

    # Do not stop at the first solution when force-near/row/column or companion
    # overlap scoring matters. The first feasible layout can be valid but worse,
    # e.g. lettuce on dill instead of the stronger carrot/lettuce pair.
    if not maximise_search and not (next_to or force_row or force_column or has_companion_objective):
        solver.parameters.stop_after_first_solution = True

    model.Maximize(sum(objective_terms))
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if _allow_soft_fallback and (next_to or force_row or force_column):
            fallback = placing_with_cp_sat(
                plants=plants,
                box_sizes=box_sizes,
                lists=lists,
                locked_plants=locked_plants,
                next_to=False,
                avoid=avoid,
                fill=fill,
                force_row=False,
                force_column=False,
                maximise_search=False,
                time_limit=max(5, min(time_limit, 12)),
                _allow_soft_fallback=False,
                no_companion_overlap=no_companion_overlap,
            )
            fallback["soft_rules_relaxed"] = True
            fallback["warning"] = "Force-near was relaxed because the larger CP-SAT soft-scoring model did not find a solution in time."
            return fallback

        return {
            "result": "No feasible solution found",
            "actual_grids": [],
            "same_grids_by_type": {},
            "plant_instances": [],
            "total_score": 0,
            "not_placed": [item["name"] for item in expanded],
        }

    chosen = {}
    for i in range(len(expanded)):
        if solver.Value(used[i]) == 1:
            for k in range(len(candidates[i])):
                if solver.Value(place[(i, k)]) == 1:
                    chosen[i] = k
                    break

    actual_grid, same_grids_by_type = render_solution(
        rows, cols, expanded, candidates, chosen, usable_cells, locked
    )

    chosen_instances = build_chosen_instance_payloads(expanded, candidates, chosen, box_ranges)

    not_placed = []
    for i in range(len(expanded)):
        if solver.Value(used[i]) == 0:
            not_placed.append(expanded[i]["name"])

    split_actual_grids = split_into_separate_grids(actual_grid, box_ranges)

    split_same_grids_by_type = {}
    for plant_name, same_grid in same_grids_by_type.items():
        split_same_grids_by_type[plant_name] = split_into_separate_grids(
            same_grid, box_ranges
        )

    result = {
        "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
        "objective": solver.ObjectiveValue(),
        "placed": len(locked_instances) + sum(solver.Value(used[i]) for i in range(len(expanded))),
        "total": len(locked_instances) + len(expanded),
        "locked_placed": len(locked_instances),
    }

    return {
        "result": result,
        "actual_grids": split_actual_grids,
        "same_grids_by_type": split_same_grids_by_type,
        "plant_instances": locked_instances + chosen_instances,
        "total_score": total_score_grid(plants, actual_grid, avoid, next_to, fill, force_row, force_column),
        "not_placed": not_placed,
    }


def run_autosort_constraint(payload):
    cell_cm = int(payload.get("cell_cm", 15))
    next_to = bool(payload.get("next_to", True))
    avoid = bool(payload.get("avoid", True))
    fill = bool(payload.get("fill", False))
    force_row = bool(payload.get("force_row", False))
    force_column = bool(payload.get("force_column", False))
    maximise_search = bool(payload.get("maximise_search", False))
    time_limit = int(payload.get("time_limit", 20))
    no_companion_overlap = bool(payload.get("no_companion_overlap", False))

    if force_row and force_column:
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

    lists = sorting_list_relationship(lists)

    return placing_with_cp_sat(
        plants=plant_lookup,
        box_sizes=box_sizes,
        lists=lists,
        locked_plants=locked_plants,
        next_to=next_to,
        avoid=avoid,
        fill=fill,
        force_row=force_row,
        force_column=force_column,
        maximise_search=maximise_search,
        time_limit=time_limit,
        no_companion_overlap=no_companion_overlap,
    )