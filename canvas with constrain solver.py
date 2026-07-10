from ortools.sat.python import cp_model

plants = {
    "tomatoe": {
        "name": "tomatoe",
        "size_same": 3,
        "size": 4,
        "helps": [],
        "helps_by": ["basil", "carrot", "onion"],
        "avoid": []
    },
    "basil": {
        "name": "basil",
        "size_same": 1,
        "size": 2,
        "helps": ["tomatoe"],
        "helps_by": [],
        "avoid": []
    },
    "carrot": {
        "name": "carrot",
        "size_same": 1,
        "size": 2,
        "helps": ["tomatoe", "lettuce", "onion"],
        "helps_by": ["lettuce", "onion"],
        "avoid": []
    },
    "lettuce": {
        "name": "lettuce",
        "size_same": 2,
        "size": 2,
        "helps": ["onion", "carrot"],
        "helps_by": ["onion", "carrot"],
        "avoid": []
    },
    "onion": {
        "name": "onion",
        "size_same": 1,
        "size": 2,
        "helps": ["tomatoe", "carrot", "lettuce"],
        "helps_by": ["carrot", "lettuce"],
        "avoid": []
    },
    "blueberry": {
        "name": "blueberry",
        "size_same": 1,
        "size": 1,
        "helps": [],
        "helps_by": [],
        "avoid": ["tomatoe"]
    }
}


def grid(a, b):
    grid_num = []
    grid_plants = []
    for _ in range(a):
        plant_line = []
        num_line = []
        for _ in range(b):
            plant_line.append("")
            num_line.append(-50)
        grid_plants.append(plant_line)
        grid_num.append(num_line)
    return grid_plants, grid_num


def checkitem(item):
    if item == "tomatoe" or item == "t":
        plant = plants["tomatoe"]
    elif item == "basil" or item == "b":
        plant = plants["basil"]
    elif item == "carrot" or item == "c":
        plant = plants["carrot"]
    elif item == "lettuce" or item == "l":
        plant = plants["lettuce"]
    elif item == "onion" or item == "o":
        plant = plants["onion"]
    elif item == "blueberry" or item == "bb":
        plant = plants["blueberry"]
    else:
        plant = None
    return plant


def listmake():
    done = False
    print("the plants we have: tomatoe, basil, carrot, lettuce, onion, blueberry")
    lists = []
    while done is not True:
        temp = []
        item = input("what plant ")
        amount = int(input("how many "))
        plant = checkitem(item)
        if plant is not None:
            temp.append(plant)
            temp.append(amount)
            lists.append(temp)
        else:
            print()
            print("error didnt add")
            print()
        isdone = input("are you done? Y or N ")
        print()
        if isdone == "Y" or isdone == "y":
            done = True
    return lists


def insertion_sort_by_size(items):
    for i in range(1, len(items)):
        key_item = items[i]
        key_size = key_item[0]["size"]
        key_amount = key_item[1]

        j = i - 1
        while (
            j >= 0 and (
                items[j][0]["size"] < key_size or
                (items[j][0]["size"] == key_size and items[j][1] > key_amount)
            )
        ):
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key_item

    return items


def sortingListrelship(lst):
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
    if cell == "":
        return []
    if isinstance(cell, list):
        return cell[:]
    return [cell]


def relation_score(a_name, b_name):
    """
    Returns:
    -1000 if avoid pair
     2 if two-way helpful
     1 if one-way helpful
     0 otherwise
    """
    if a_name == b_name:
        return 0

    a = plants[a_name]
    b = plants[b_name]

    if b_name in a.get("avoid", []) or a_name in b.get("avoid", []):
        return -1000

    a_forward = (b_name in a.get("helps", [])) or (b_name in a.get("helps_by", []))
    b_forward = (a_name in b.get("helps", [])) or (a_name in b.get("helps_by", []))

    if a_forward and b_forward:
        return 2
    if a_forward or b_forward:
        return 1
    return 0

# sees if 2 different plant types can or cant overlap (same plant type handled elsewhere)
def can_overlap_types(a_name, b_name):
    if a_name == b_name:
        return True
    return relation_score(a_name, b_name) > 0


def expand_items(lists):
    expanded = []
    for item in lists:
        plant = item[0]
        amount = item[1]
        for copy_idx in range(amount):
            expanded.append({
                "instance_id": len(expanded),
                "name": plant["name"],
                "size": plant["size"],
                "size_same": plant["size_same"],
                "copy_idx": copy_idx
            })
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


def placements_overlap(cells_a, cells_b):
    return len(set(cells_a).intersection(set(cells_b))) > 0


def shared_cell_count(cells_a, cells_b):
    return len(set(cells_a).intersection(set(cells_b)))


def side_contact_count(cells_a, cells_b):
    """
    Counts touching edges between two plants.
    Overlapping cells do not count as side contact.
    """
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


def build_candidate_positions(rows, cols, expanded):
    candidates = {}
    for i, plant in enumerate(expanded):
        candidates[i] = []
        size = plant["size"]
        size_same = plant["size_same"]

        for x in range(rows - size + 1):
            for y in range(cols - size + 1):
                candidates[i].append({
                    "x": x,
                    "y": y,
                    "actual_cells": get_actual_cells(x, y, size),
                    "same_cells": get_same_cells(x, y, size_same)
                })

    return candidates


def add_and_var(model, a, b, name):
    """
    Returns bool var both where both == 1 iff a == 1 and b == 1
    """
    both = model.NewBoolVar(name)
    model.Add(both <= a)
    model.Add(both <= b)
    model.Add(both >= a + b - 1)
    return both


def render_solution(rows, cols, expanded, candidates, chosen):
    actual_grid = [["" for _ in range(cols)] for _ in range(rows)]

    # Build actual grid
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

    plant_names = sorted(set(item["name"] for item in expanded))

    for plant_name in plant_names:
        same_grid = [row[:] for row in actual_grid]

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


def printing(grids):
    for j in grids:
        print(j)


def placing_with_cp_sat(grid_plants, lists, next_to=True, avoid=True, time_limit=20):
    rows = len(grid_plants)
    cols = len(grid_plants[0])

    expanded = expand_items(lists)
    candidates = build_candidate_positions(rows, cols, expanded)

    model = cp_model.CpModel()

    place = {}
    used = {}

    # Variable creation
    for i in range(len(expanded)):
        used[i] = model.NewBoolVar(f"used_{i}")

        for k in range(len(candidates[i])):
            place[(i, k)] = model.NewBoolVar(f"place_{i}_{k}")

        # either choose exactly one candidate, or skip this plant
        model.Add(sum(place[(i, k)] for k in range(len(candidates[i]))) == used[i])

    # Max 2 plants per actual cell
    for r in range(rows):
        for c in range(cols):
            cover_vars = []
            for i in range(len(expanded)):
                for k, cand in enumerate(candidates[i]):
                    if (r, c) in cand["actual_cells"]:
                        cover_vars.append(place[(i, k)])
            if cover_vars:
                model.Add(sum(cover_vars) <= 2)

    # Same plant copies cannot overlap in size_same region
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

    # Incompatible overlap bans + objective
    objective_terms = []

    BIG_PLACED = 10000
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

                    # Different-type overlap rules
                    if actual_overlap_cells > 0 and name_i != name_j:
                        if not can_overlap_types(name_i, name_j):
                            model.Add(place[(i, k)] + place[(j, l)] <= 1)
                        else:
                            rel = relation_score(name_i, name_j)
                            if rel > 0:
                                both = add_and_var(
                                    model,
                                    place[(i, k)],
                                    place[(j, l)],
                                    f"ov_{i}_{k}_{j}_{l}"
                                )
                                objective_terms.append(rel * actual_overlap_cells * both)

                    # Same-type side-neighbour reward
                    if next_to and name_i == name_j:
                        contacts = side_contact_count(
                            cand_i["actual_cells"],
                            cand_j["actual_cells"]
                        )
                        if contacts > 0:
                            both = add_and_var(
                                model,
                                place[(i, k)],
                                place[(j, l)],
                                f"side_{i}_{k}_{j}_{l}"
                            )
                            objective_terms.append(contacts * both)

                    # Avoid side-neighbour penalty
                    if avoid:
                        bad_pair = (
                            name_j in plants[name_i].get("avoid", []) or
                            name_i in plants[name_j].get("avoid", [])
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
                                    f"avoid_{i}_{k}_{j}_{l}"
                                )
                                objective_terms.append(-4 * contacts * both)

    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 1

    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return grid_plants, {}, "No feasible solution found"

    chosen = {}
    for i in range(len(expanded)):
        if solver.Value(used[i]) == 1:
            for k in range(len(candidates[i])):
                if solver.Value(place[(i, k)]) == 1:
                    chosen[i] = k
                    break

    actual_grid, same_grids_by_type = render_solution(rows, cols, expanded, candidates, chosen)

    result = {
        "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
        "objective": solver.ObjectiveValue(),
        "placed": sum(solver.Value(used[i]) for i in range(len(expanded))),
        "total": len(expanded)
    }

    return actual_grid, same_grids_by_type, result


def total_score_grid(grid, avoid, next_to):
    score = 0
    rows = len(grid)
    cols = len(grid[0])

    for i in range(rows):
        for j in range(cols):
            cell = cell_to_list(grid[i][j])

            if len(cell) == 1:
                score += 0

            if len(cell) == 2:
                plant1_name = cell[0]
                plant2_name = cell[1]

                plant1 = plants[plant1_name]
                plant2 = plants[plant2_name]

                if plant2_name in plant1.get("avoid", []):
                    score -= 1000
                if plant1_name in plant2.get("avoid", []):
                    score -= 1000

                p1_forward = (plant2_name in plant1.get("helps", [])) or (plant2_name in plant1.get("helps_by", []))
                p2_forward = (plant1_name in plant2.get("helps", [])) or (plant1_name in plant2.get("helps_by", []))

                if p1_forward and p2_forward:
                    score += 2
                elif p1_forward or p2_forward:
                    score += 1

            # check only right and down neighbours to avoid double counting
            neighbours = []
            if i + 1 < rows:
                neighbours.append(cell_to_list(grid[i+1][j]))
            if j + 1 < cols:
                neighbours.append(cell_to_list(grid[i][j+1]))

            for plant_name in cell:
                plant = plants[plant_name]

                for neighbour_cell in neighbours:
                    for other_name in neighbour_cell:
                        if next_to and other_name == plant_name:
                            score += 1

                        if avoid and other_name in plant.get("avoid", []):
                            score -= 4

    return score


def main():
    a = int(input(("what is the grid size a in axb")))
    b = int(input(("what is the grid size b in axb")))
    #a = 7
    #b =10
    
    grid_plants, grid_num = grid(a, b)
    
    #lists = [[plants["tomatoe"],2],[plants["basil"],1],[plants["carrot"],6],[plants["lettuce"],2],[plants["onion"],10],[plants["blueberry"],2]]
    #lists = [[plants["tomatoe"],2],[plants["blueberry"],1]]

    next_Spacing = input(("want yoru plants to be more closely together"))
    if next_Spacing == "T" or next_Spacing == "t":
        next_to = True
    else:
        next_to = False
    #next_to = True
    avoid_space = input(("want an extra space around plants that need cant be placed with each other"))
    if avoid_space == "T" or avoid_space == "t":
        avoid = True
    else:
        avoid = False
    #avoid = True

    lists = listmake()
    

    

    lists = sortingListrelship(lists)

    grid_plants, same_grids_by_type, result = placing_with_cp_sat(
        grid_plants,
        lists,
        next_to=next_to,
        avoid=avoid,
        time_limit=20
    )

    print(result)
    print("\nACTUAL GRID:")
    printing(grid_plants)

    for plant_name, same_grid in same_grids_by_type.items():
        print(f"\nSAME GRID FOR {plant_name.upper()}:")
        printing(same_grid)


main()