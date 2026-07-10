export const CELL_SIZE_PX = 32;
export const CELL_CM = 15;

export function snapToGrid(value) {
  return Math.round(value);
}

export function makeBox(type = "square", existingCount = 0) {
  const id = `box_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  const offset = existingCount * 2;

  if (type === "rectangle") {
    return {
      id,
      type,
      x: offset,
      y: offset,
      w: 6,
      h: 4,
    };
  }

  return {
    id,
    type: "square",
    x: offset,
    y: offset,
    w: 4,
    h: 4,
  };
}

export function getBoardBounds(boxes) {
  if (!boxes.length) {
    return { cols: 20, rows: 20 };
  }

  const maxX = Math.max(...boxes.map((b) => b.x + b.w));
  const maxY = Math.max(...boxes.map((b) => b.y + b.h));

  return {
    cols: Math.max(20, maxX + 2),
    rows: Math.max(20, maxY + 2),
  };
}

export function boxesToSolverPayload(boxes) {
  return boxes.map((box) => ({
    rows: box.h,
    cols: box.w,
  }));
}

export function plantSpacingToCells(plant) {
  const spacingCm = Number(plant?.spacing_between_rows ?? 0);
  return Math.max(1, Math.ceil(spacingCm / CELL_CM));
}

export function plantSameSpacingToCells(plant) {
  const spacingCm = Number(plant?.spacing_in_rows ?? 0);
  return Math.max(1, Math.ceil(spacingCm / CELL_CM));
}

export function rectsOverlap(a, b) {
  return !(
    a.col + a.width <= b.col ||
    b.col + b.width <= a.col ||
    a.row + a.height <= b.row ||
    b.row + b.height <= a.row
  );
}

export function pointToCell(
  clientX,
  clientY,
  containerRect,
  scaledCellSize,
  scrollLeft = 0,
  scrollTop = 0
) {
  return {
    col: snapToGrid((clientX - containerRect.left + scrollLeft) / scaledCellSize),
    row: snapToGrid((clientY - containerRect.top + scrollTop) / scaledCellSize),
  };
}

export function findBoxIndexAtCell(boxes, row, col) {
  return boxes.findIndex(
    (box) =>
      col >= box.x &&
      col < box.x + box.w &&
      row >= box.y &&
      row < box.y + box.h
  );
}

export function clampPlantToBox(plant, box, nextRow, nextCol) {
  return {
    row: Math.max(box.y, Math.min(box.y + box.h - plant.height, nextRow)),
    col: Math.max(box.x, Math.min(box.x + box.w - plant.width, nextCol)),
  };
}

export function buildLockedPlantsPayload(plantInstances, boxes) {
  return plantInstances
    .filter((plant) => plant.locked)
    .map((plant) => {
      const box = boxes[plant.boxIndex];
      if (!box) return null;

      return {
        name: plant.name,
        box_index: plant.boxIndex,
        row: plant.localRow,
        col: plant.localCol,
        width: plant.width,
        height: plant.height,
      };
    })
    .filter(Boolean);
}

export function buildAutosortPlantsPayload(plantInstances) {
  const counts = {};

  for (const plant of plantInstances) {
    if (plant.locked) continue;
    counts[plant.name] = (counts[plant.name] || 0) + 1;
  }

  return Object.entries(counts).map(([name, amount]) => ({
    name,
    amount,
  }));
}

export function getPlantAbsolutePosition(plant, boxes) {
  const box = boxes[plant.boxIndex];
  if (!box) {
    return {
      row: plant.localRow,
      col: plant.localCol,
    };
  }

  return {
    row: box.y + plant.localRow,
    col: box.x + plant.localCol,
  };
}

export function withAbsolutePlantPosition(plant, boxes) {
  const absolute = getPlantAbsolutePosition(plant, boxes);
  return {
    ...plant,
    boxIndex: plant.boxIndex,
    row: absolute.row,
    col: absolute.col,
  };
}

export function makePlantInstance(plant, boxIndex, localRow = 0, localCol = 0) {
  const size = plantSpacingToCells(plant);
  const sizeSame = plantSameSpacingToCells(plant);

  return {
    id: `plant_${Date.now()}_${Math.random().toString(16).slice(2)}`,
    plantId: plant.id,
    name: plant.name,
    boxIndex,
    localRow,
    localCol,
    width: size,
    height: size,
    sizeSame,
    locked: false,
  };
}

export function clampPlantLocalToBox(plant, box, nextLocalRow, nextLocalCol) {
  return {
    localRow: Math.max(0, Math.min(box.h - plant.height, nextLocalRow)),
    localCol: Math.max(0, Math.min(box.w - plant.width, nextLocalCol)),
  };
}

function getActualRectAbsolute(plant, boxes) {
  const box = boxes[plant.boxIndex];
  return {
    row: box.y + plant.localRow,
    col: box.x + plant.localCol,
    width: plant.width,
    height: plant.height,
  };
}

function getUniquePlantTypes(plants) {
  return new Set(plants.map((p) => String(p.name).toLowerCase()));
}

function getSameRectAbsolute(plant, boxes) {
  const box = boxes[plant.boxIndex];
  const sizeSame = Math.max(1, Number(plant.sizeSame ?? plant.width));

  const rowOffset = Math.floor((plant.height - sizeSame) / 2);
  const colOffset = Math.floor((plant.width - sizeSame) / 2);

  return {
    row: box.y + plant.localRow + rowOffset,
    col: box.x + plant.localCol + colOffset,
    width: sizeSame,
    height: sizeSame,
  };
}

function getCoveredCells(rect) {
  const cells = [];
  for (let row = rect.row; row < rect.row + rect.height; row++) {
    for (let col = rect.col; col < rect.col + rect.width; col++) {
      cells.push(`${row}:${col}`);
    }
  }
  return cells;
}

function rectContainsCell(rect, cellKey) {
  const [rowRaw, colRaw] = cellKey.split(":");
  const row = Number(rowRaw);
  const col = Number(colRaw);

  return (
    row >= rect.row &&
    row < rect.row + rect.height &&
    col >= rect.col &&
    col < rect.col + rect.width
  );
}

function normaliseName(name) {
  return String(name || "").trim().toLowerCase();
}

function getPlantDataByName(plantsData, name) {
  const key = normaliseName(name);
  return plantsData.find((plant) => normaliseName(plant.name) === key);
}

function listHasName(list, name) {
  const key = normaliseName(name);
  return Array.isArray(list) && list.some((item) => normaliseName(item) === key);
}

export function plantsCanOverlap(candidatePlant, otherPlant, plantsData = []) {
  if (candidatePlant.name === otherPlant.name) return true;

  const candidateData = getPlantDataByName(plantsData, candidatePlant.name);
  const otherData = getPlantDataByName(plantsData, otherPlant.name);

  // Be safe if the API data has not loaded yet.
  if (!candidateData || !otherData) return false;

  const candidateAvoidsOther = listHasName(candidateData.plants_avoid_names, otherData.name);
  const otherAvoidsCandidate = listHasName(otherData.plants_avoid_names, candidateData.name);

  if (candidateAvoidsOther || otherAvoidsCandidate) return false;

  const candidateLikesOther =
    listHasName(candidateData.companion_helps_names, otherData.name) ||
    listHasName(candidateData.companion_helped_by_names, otherData.name);

  const otherLikesCandidate =
    listHasName(otherData.companion_helps_names, candidateData.name) ||
    listHasName(otherData.companion_helped_by_names, candidateData.name);

  return candidateLikesOther || otherLikesCandidate;
}

export function placedPlantCollidesUsingBoxes(
  candidatePlant,
  plantInstances,
  boxes,
  ignoreId = null,
  plantsData = []
) {
  const candidateActual = getActualRectAbsolute(candidatePlant, boxes);
  const candidateSame = getSameRectAbsolute(candidatePlant, boxes);
  const candidateCells = getCoveredCells(candidateActual);

  // Hard display rule: allow many plants in a cell, but only up to 2 plant TYPES.
  for (const cellKey of candidateCells) {
    const plantsInCell = [candidatePlant];

    for (const plant of plantInstances) {
      if (plant.id === ignoreId) continue;

      const otherActual = getActualRectAbsolute(plant, boxes);
      if (rectContainsCell(otherActual, cellKey)) {
        plantsInCell.push(plant);
      }
    }

    const uniqueTypes = getUniquePlantTypes(plantsInCell);

    if (uniqueTypes.size > 2) {
      return true;
    }
  }

  return plantInstances.some((plant) => {
    if (plant.id === ignoreId) return false;

    const otherActual = getActualRectAbsolute(plant, boxes);
    const otherSame = getSameRectAbsolute(plant, boxes);

    // Same species: allow outer spacing overlap, but not same-core overlap.
    if (plant.name === candidatePlant.name) {
      return rectsOverlap(candidateSame, otherSame);
    }

    if (!rectsOverlap(candidateActual, otherActual)) return false;

    // Different species may overlap only when they are compatible companions.
    return !plantsCanOverlap(candidatePlant, plant, plantsData);
  });
}

export function findFirstFitForPlant(
  plant,
  boxes,
  plantInstances,
  plantsData = [],
  preferCompanionOverlap = false
) {
  const positions = [];

  if (preferCompanionOverlap) {
    for (const existingPlant of plantInstances) {
      if (!plantsCanOverlap(plant, existingPlant, plantsData)) continue;

      positions.push({
        boxIndex: existingPlant.boxIndex,
        localRow: existingPlant.localRow,
        localCol: existingPlant.localCol,
      });
    }
  }

  for (let boxIndex = 0; boxIndex < boxes.length; boxIndex++) {
    const box = boxes[boxIndex];

    if (plant.width > box.w || plant.height > box.h) continue;

    for (let localRow = 0; localRow <= box.h - plant.height; localRow++) {
      for (let localCol = 0; localCol <= box.w - plant.width; localCol++) {
        positions.push({ boxIndex, localRow, localCol });
      }
    }
  }

  const seen = new Set();

  for (const position of positions) {
    const box = boxes[position.boxIndex];
    if (!box) continue;
    if (plant.width > box.w || plant.height > box.h) continue;

    const key = `${position.boxIndex}-${position.localRow}-${position.localCol}`;
    if (seen.has(key)) continue;
    seen.add(key);

    const candidate = {
      ...plant,
      boxIndex: position.boxIndex,
      localRow: position.localRow,
      localCol: position.localCol,
    };

    if (!placedPlantCollidesUsingBoxes(candidate, plantInstances, boxes, null, plantsData)) {
      return position;
    }
  }

  return null;
}
