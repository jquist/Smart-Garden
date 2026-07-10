import random
plants = {
    "tomatoe" : {
        "name": "tomatoe",
        "size_same": 3,
        "size": 4,
        "helps": [],
        "helps_by": [
            "basil",
            "carrot",
            "onion"
        ],
        "avoid": []
    },
    "basil" : {
        "name": "basil",
        "size_same": 1,
        "size": 2,
        "helps": [
            "tomatoe"
        ],
        "helps_by": [],
        "avoid": []
    },
    "carrot" : {
        "name": "carrot",
        "size_same": 1,
        "size": 2,
        "helps": [
            "tomatoe",
            "lettuce",
            "onion"
        ],
        "helps_by": [
            "lettuce",
            "onion"
        ],
        "avoid": []
    },
    "lettuce" : {
        "name": "lettuce",
        "size_same": 2,
        "size": 2,
        "helps": [
            "onion",
            "carrot"
        ],
        "helps_by": [
            "onion",
            "carrot"
        ],
        "avoid": []
    },
    "onion" : {
        "name": "onion",
        "size_same": 1,
        "size": 2,
        "helps": [
            "tomatoe",
            "carrot",
            "lettuce"
        ],
        "helps_by": [
            "carrot",
            "lettuce"
        ],
        "avoid": []
    },
    "blueberry" : {
        "name": "blueberry",
        "size_same": 1,
        "size": 1,
        "helps": [],
        "helps_by": [],
        "avoid": [
            "tomatoe"
        ]
    }
}

def grid(a,b):
    grid_num=[]
    grid_plants = []
    for i in range(0,a):
        plant_line = []
        num_line=[]
        for j in range(0,b):
            plant_line.append("")
            num_line.append(-50)
        grid_plants.append(plant_line)
        grid_num.append(num_line)       
    return grid_plants,grid_num

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
    else:
        plant = None
    return plant

def listmake():
    done = False
    print("the plants we have: tomatoe, basil, carrot, lettuce, onion")
    lists = []
    while done != True:
        temp=[]
        item = input(("what plant"))
        amount = int(input(("how many")))
        plant = checkitem(item)
        if plant != None:
            temp.append(plant)
            temp.append(amount)
            lists.append(temp)
        else:
            print()
            print("error didnt add")
            print()
        isdone = input(print("are you done? Y or N"))
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
        while (j >= 0 and (items[j][0]["size"] < key_size or(items[j][0]["size"] == key_size and items[j][1] > key_amount))):
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key_item

    return items

def sortingListrelship(list):
    rel1 = []
    rel2 = []
    rel0 = []
    relN = []
    new_list = []

    names_in_list = [x[0]["name"] for x in list]

    for i in list:
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

def sortingListsize(list):
    list = insertion_sort_by_size(list) 
    return list

def cell_to_list(cell):
    if cell == "":
        return []
    if isinstance(cell, list):
        return cell[:]
    return [cell]  # string

def relation_score(a, b, placing_plant):
    """
    Score interaction between 'placing_plant' and an existing plant name 'b'.
    a = placing plant name
    b = existing plant name
    returns: large negative for avoid, +2/+1/0 otherwise
    """
    if a == b:
        return -10**6  # disallow same plant overlap completely

    helps = placing_plant.get("helps", [])
    helps_by = placing_plant.get("helps_by", [])

    avoid = placing_plant.get("avoid", [])
    if b in avoid:
        return -1000

    a_to_b = (b in helps)
    b_to_a = (b in helps_by)

    if a_to_b and b_to_a:
        return 2
    if a_to_b or b_to_a:
        return 1
    return 0

def can_overlap_with(cell, placing_plant):
    """
    Enforce: max 2 per cell, overlap only if relation is 1 or 2 with ALL existing.
    """
    existing = cell_to_list(cell)
    if not existing:
        return True
    if len(existing) >= 2:
        return False

    a = placing_plant["name"]
    avoid = placing_plant.get("avoid", [])

    for b in existing:
        if b in avoid:
            return False
        sc = relation_score(a, b, placing_plant)
        if sc <= 0:  # only allow overlap if 1-way or 2-way
            return False
    return True

def has_plant(cell,name):
    cell_plant = cell_to_list(cell)
    return name in cell_plant

def avoid_penalty(grid, x, y, size, placing_plant):
    penalty = 0
    rows = len(grid)
    cols = len(grid[0])

    avoid = placing_plant.get("avoid", [])
    if not avoid:
        return 0

    # check the 1-cell border around the size x size placement
    for r in range(x - 1, x + size + 1):
        for c in range(y - 1, y + size + 1):

            # skip out of bounds
            if r < 0 or r >= rows or c < 0 or c >= cols:
                continue

            # skip inside the actual footprint
            if x <= r < x + size and y <= c < y + size:
                continue

            cell = cell_to_list(grid[r][c])

            for plant_name in cell:
                if plant_name in avoid:
                    penalty -= 1

    return penalty

def side_adds(grid, x, y, size, placing_name):
    num = 0
    rows = len(grid)
    cols = len(grid[0])

    for i in range(size):
        if x - 1 >= 0 and y + i < cols:
            if has_plant(grid[x - 1][y + i], placing_name):
                num += 1

        if x + size < rows and y + i < cols:
            if has_plant(grid[x + size][y + i], placing_name):
                num += 1

        if y - 1 >= 0 and x + i < rows:
            if has_plant(grid[x + i][y - 1], placing_name):
                num += 1

        if y + size < cols and x + i < rows:
            if has_plant(grid[x + i][y + size], placing_name):
                num += 1

    return num

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

def get_candidaties(actual, same, is_same, num, item,next_to,avoid):
    rows = len(actual)
    cols = len(actual[0])
    size = item[0]["size"]
    placing_plant = item[0]
    placing_name = placing_plant["name"]

    grid_to_use = same if is_same else actual

    def score_cell(cell):
        existing = cell_to_list(cell)
        if not existing:
            return 0

        # If already contains this plant -> disallow (hard)
        if placing_name in existing:
            return -10**6

        # If max capacity reached -> disallow (hard)
        if len(existing) >= 2:
            return -10**6

        # Score based on relations to occupants
        s = 0
        for b in existing:
            rs = relation_score(placing_name, b, placing_plant)
            s += rs
        return s

    for x in range(rows):
        for y in range(cols):
            num[x][y] = score_cell(grid_to_use[x][y])
            if next_to:
                num[x][y] += side_adds(grid_to_use,x,y,size,placing_name)


    best = -10**18
    best_x, best_y = None, None
    legal = []

    for x in range(rows - size + 1):
        for y in range(cols - size + 1):
            local = []
            # HARD CHECK: every footprint cell must be placeable
            ok = True
            for ix in range(size):
                for iy in range(size):
                    if not can_overlap_with(grid_to_use[x+ix][y+iy], placing_plant):
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue

            s = 0
            for ix in range(size):
                for iy in range(size):
                    s += num[x + ix][y + iy]
            if avoid == True:
                s += avoid_penalty(actual, x, y, size, placing_plant)

            local.append(x)
            local.append(y)
            local.append(s)
            legal.append(local)

    return legal

def prune_candidates(cands, k=3):
    if not cands:
        return []

    best = max(c[2] for c in cands)
    best_list = [c for c in cands if c[2] == best]

    random.shuffle(best_list)

    if len(best_list) <= k:
        return best_list

    return best_list[:k]

def search_best(actual_grid, same_grid, remaining_plants, next_to, avoid, best_result, total_count, k=3, prev_name=None):
    placed_count = total_count - len(remaining_plants)

    if not remaining_plants:
        score = total_score_grid(actual_grid,avoid,next_to)

        if (placed_count > best_result["placed"]) or (
            placed_count == best_result["placed"] and score > best_result["score"]
        ):
            best_result["placed"] = placed_count
            best_result["score"] = score
            best_result["grid"] = [row[:] for row in actual_grid]
            best_result["same"] = [row[:] for row in same_grid]
        return

    plant, is_same = remaining_plants[0]
    current_name = plant["name"]

    # reset same_grid when plant type changes
    if prev_name is None or current_name != prev_name:
        same_grid = [row[:] for row in actual_grid]

    item = [plant, 1]

    num = [[-50 for _ in range(len(actual_grid[0]))] for _ in range(len(actual_grid))]
    cands = get_candidaties(actual_grid, same_grid, is_same, num, item, next_to, avoid)

    if not cands:
        score = total_score_grid(actual_grid,avoid,next_to)

        if (placed_count > best_result["placed"]) or (
            placed_count == best_result["placed"] and score > best_result["score"]
        ):
            best_result["placed"] = placed_count
            best_result["score"] = score
            best_result["grid"] = [row[:] for row in actual_grid]
            best_result["same"] = [row[:] for row in same_grid]
        return

    cands = prune_candidates(cands, k)

    for cand in cands:
        x, y, _ = cand
        new_actual, new_same = place_copy(actual_grid, same_grid, plant, x, y)
        search_best(new_actual, new_same, remaining_plants[1:], next_to, avoid, best_result, total_count, k, current_name)

def placing_with_backtracking(grid_plants, lists, next_to, avoid, k=3):
    actual_grid = [row[:] for row in grid_plants]
    same_grid = [row[:] for row in grid_plants]

    expanded = expand_items(lists)

    best_result = {
        "score": -10**18,
        "grid": None,
        "same": None,
        "placed": -1
    }

    search_best(actual_grid, same_grid, expanded, next_to, avoid, best_result, len(expanded), k)

    if best_result["grid"] is None:
        return actual_grid, same_grid, ["No complete solution found"]

    return best_result["grid"], best_result["same"], best_result["score"]


def expand_items(lists):
    expanded = []
    for item in lists:
        plant = item[0]
        amount = item[1]
        for i in range(amount):
            expanded.append([plant, i > 0])
    return expanded

def place_copy(actual_grid, same_grid, plant, x, y):
    new_actual = [row[:] for row in actual_grid]
    new_same = [row[:] for row in same_grid]

    name = plant["name"]
    size = plant["size"]
    size_same = plant["size_same"]

    for r in range(size):
        for c in range(size):
            actual_existing = cell_to_list(new_actual[x+r][y+c])

            if name not in actual_existing:
                actual_existing.append(name)

            if len(actual_existing) == 0:
                new_actual[x+r][y+c] = ""
            elif len(actual_existing) == 1:
                new_actual[x+r][y+c] = actual_existing[0]
            else:
                new_actual[x+r][y+c] = actual_existing[:2]

            if r < size_same and c < size_same:
                same_existing = cell_to_list(new_same[x+r][y+c])

                if name not in same_existing:
                    same_existing.append(name)

                if len(same_existing) == 0:
                    new_same[x+r][y+c] = ""
                elif len(same_existing) == 1:
                    new_same[x+r][y+c] = same_existing[0]
                else:
                    new_same[x+r][y+c] = same_existing[:2]

    return new_actual, new_same

def printing(grids):
    for j in grids:
        print(j)



def main():
    #a = int(input(("what is the grid size a in axb")))
    #b = int(input(("what is the grid size b in axb")))
    a = 7
    b =10
    grid_plants = []
    grid_num=[]
    grid_plants,grid_num = grid(a,b)
    #lists = listmake()
    lists = [[plants["tomatoe"],2],[plants["basil"],1],[plants["carrot"],6],[plants["lettuce"],2],[plants["onion"],10],[plants["blueberry"],2]]
    #lists = [[plants["tomatoe"],2],[plants["blueberry"],1]]

    #next_Spacing = int(input(("want yoru plants to be more closely together")))
    #if next_Spacing == "T" or next_Spacing == "t":
    #    next_to = True
    #else:S
    #    next_to = False
    next_to = True
    #avoid_space = int(input(("want an extra space around plants that need cant be placed with each other")))
    #if avoid_space == "T" or next_Spacing == "t":
    #    avoid = True
    #else:
    #    avoid = False
    avoid = True

    

    lists = sortingListrelship(lists)
    grid_plants, same_grid, cant_place = placing_with_backtracking(grid_plants, lists, next_to, avoid, k=3)    
    print(cant_place)
    print()
    printing(grid_plants)
    print()
    printing(same_grid)

main()