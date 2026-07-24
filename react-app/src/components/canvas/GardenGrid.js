import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CELL_SIZE_PX,
  getBoardBounds,
  snapToGrid,
  pointToCell,
  findBoxIndexAtCell,
  withAbsolutePlantPosition,
  clampPlantLocalToBox,
  placedPlantCollidesUsingBoxes,
  makePlantInstance,
} from "./canvasUtils";

const CELL_SIZE_CM = 15;

function GardenGrid({
  boxes,
  setBoxes,
  selectedBoxId,
  setSelectedBoxId,
  sortResult,
  plantInstances,
  setPlantInstances,
  plantsData,
  acceptedDropSources = ["plants-panel"],
  itemLabel = "plant",
  boardTip = null,
}) {
  const bounds = useMemo(() => getBoardBounds(boxes), [boxes]);

  const [draggingBoxId, setDraggingBoxId] = useState(null);
  const [resizingBoxId, setResizingBoxId] = useState(null);
  const [draggingPlantId, setDraggingPlantId] = useState(null);
  const [selectedPlantId, setSelectedPlantId] = useState(null);
  const [zoom, setZoom] = useState(1);

  const actionStartRef = useRef(null);
  const dragMovedRef = useRef(false);
  const boardRef = useRef(null);

  const scaledCellSize = CELL_SIZE_PX * zoom;

  const absolutePlantInstances = useMemo(
    () => plantInstances.map((plant) => withAbsolutePlantPosition(plant, boxes)),
    [plantInstances, boxes]
  );

  const selectedPlant = useMemo(
    () => plantInstances.find((plant) => plant.id === selectedPlantId) || null,
    [plantInstances, selectedPlantId]
  );

  function shortLabel(name) {
    return String(name || "");
  }

  function handleMouseDownBox(e, box) {
    e.preventDefault();
    e.stopPropagation();

    setSelectedBoxId(box.id);
    setSelectedPlantId(null);
    setDraggingBoxId(box.id);
    setResizingBoxId(null);
    setDraggingPlantId(null);

    actionStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      startX: box.x,
      startY: box.y,
    };
  }

  function handleMouseDownResize(e, box) {
    e.preventDefault();
    e.stopPropagation();

    setSelectedBoxId(box.id);
    setSelectedPlantId(null);
    setResizingBoxId(box.id);
    setDraggingBoxId(null);
    setDraggingPlantId(null);

    actionStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      startW: box.w,
      startH: box.h,
    };
  }

  function handleMouseDownPlant(e, plant) {
    e.preventDefault();
    e.stopPropagation();

    setDraggingPlantId(plant.id);
    setSelectedPlantId(plant.id);
    setSelectedBoxId(null);
    setDraggingBoxId(null);
    setResizingBoxId(null);

    dragMovedRef.current = false;

    actionStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      startLocalRow: plant.localRow,
      startLocalCol: plant.localCol,
      boxIndex: plant.boxIndex,
    };
  }

  function handleMouseMove(e) {
    const action = actionStartRef.current;
    if (!action) return;

    const dxPx = e.clientX - action.mouseX;
    const dyPx = e.clientY - action.mouseY;

    const dxCells = snapToGrid(dxPx / scaledCellSize);
    const dyCells = snapToGrid(dyPx / scaledCellSize);

    if (Math.abs(dxPx) > 3 || Math.abs(dyPx) > 3) {
      dragMovedRef.current = true;
    }

    if (draggingBoxId) {
      const nextX = Math.max(0, action.startX + dxCells);
      const nextY = Math.max(0, action.startY + dyCells);

      setBoxes((prev) =>
        prev.map((box) =>
          box.id === draggingBoxId ? { ...box, x: nextX, y: nextY } : box
        )
      );
      return;
    }

    if (resizingBoxId) {
      const nextW = Math.max(1, action.startW + dxCells);
      const nextH = Math.max(1, action.startH + dyCells);

      setBoxes((prev) =>
        prev.map((box) =>
          box.id === resizingBoxId ? { ...box, w: nextW, h: nextH } : box
        )
      );
      return;
    }

    if (draggingPlantId) {
      if (!boardRef.current) return;

      const rect = boardRef.current.getBoundingClientRect();
      const { col, row } = pointToCell(
        e.clientX,
        e.clientY,
        rect,
        scaledCellSize,
        boardRef.current.scrollLeft,
        boardRef.current.scrollTop
      );
      const targetBoxIndex = findBoxIndexAtCell(boxes, row, col);

      setPlantInstances((prev) =>
        prev.map((plant) => {
          if (plant.id !== draggingPlantId) return plant;
          if (targetBoxIndex === -1) return plant;

          const targetBox = boxes[targetBoxIndex];
          if (!targetBox) return plant;

          const unclampedLocalRow = row - targetBox.y;
          const unclampedLocalCol = col - targetBox.x;

          const clamped = clampPlantLocalToBox(
            plant,
            targetBox,
            unclampedLocalRow,
            unclampedLocalCol
          );

          const candidate = {
            ...plant,
            boxIndex: targetBoxIndex,
            localRow: clamped.localRow,
            localCol: clamped.localCol,
          };

          if (placedPlantCollidesUsingBoxes(candidate, prev, boxes, plant.id, plantsData)) {
            return plant;
          }

          return candidate;
        })
      );
    }
  }

  function handleMouseUp() {
    setDraggingBoxId(null);
    setResizingBoxId(null);
    setDraggingPlantId(null);
    actionStartRef.current = null;
  }

  function zoomIn() {
    setZoom((prev) => Math.min(2.5, Number((prev + 0.1).toFixed(2))));
  }

  function zoomOut() {
    setZoom((prev) => Math.max(0.5, Number((prev - 0.1).toFixed(2))));
  }

  function resetZoom() {
    setZoom(1);
  }

  function handleWheel(e) {
    if (!e.ctrlKey) return;
    e.preventDefault();

    if (e.deltaY < 0) zoomIn();
    else zoomOut();
  }

  function handleDrop(e) {
    e.preventDefault();

    const raw = e.dataTransfer.getData("application/json");
    if (!raw) return;

    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return;
    }

    if (!acceptedDropSources.includes(parsed?.source)) return;
    if (!boardRef.current) return;

    const plantData = plantsData.find((plant) => plant.id === parsed.plantId);
    if (!plantData) return;

    const rect = boardRef.current.getBoundingClientRect();
    const { col, row } = pointToCell(
      e.clientX,
      e.clientY,
      rect,
      scaledCellSize,
      boardRef.current.scrollLeft,
      boardRef.current.scrollTop
    );
    const boxIndex = findBoxIndexAtCell(boxes, row, col);

    if (boxIndex === -1) return;

    const box = boxes[boxIndex];
    const newPlant = {
      ...makePlantInstance(plantData, boxIndex, row - box.y, col - box.x),
      ...(parsed.kind ? { kind: parsed.kind } : {}),
    };

    const clamped = clampPlantLocalToBox(
      newPlant,
      box,
      newPlant.localRow,
      newPlant.localCol
    );

    const finalPlant = {
      ...newPlant,
      localRow: clamped.localRow,
      localCol: clamped.localCol,
    };

    if (placedPlantCollidesUsingBoxes(finalPlant, plantInstances, boxes, null, plantsData)) {
      return;
    }

    setPlantInstances((prev) => [...prev, finalPlant]);
  }

  function handleDragOver(e) {
    e.preventDefault();
  }

  function togglePlantLocked(plantId) {
    setPlantInstances((prev) =>
      prev.map((plant) =>
        plant.id === plantId ? { ...plant, locked: !plant.locked } : plant
      )
    );
  }

  const removePlantInstance = useCallback((plantId) => {
    setPlantInstances((prev) => prev.filter((plant) => plant.id !== plantId));
    setSelectedPlantId((prev) => (prev === plantId ? null : prev));
  }, [setPlantInstances]);

  function deleteSelectedPlant() {
    if (!selectedPlant) return;
    removePlantInstance(selectedPlant.id);
  }

  useEffect(() => {
    function handleKeyDown(e) {
      if (!selectedPlantId) return;

      const isDeleteKey = e.key === "Delete" || e.key === "Backspace";
      if (!isDeleteKey) return;

      const activeTag = String(document.activeElement?.tagName || "").toLowerCase();
      const isTyping =
        activeTag === "input" ||
        activeTag === "textarea" ||
        activeTag === "select" ||
        document.activeElement?.isContentEditable;

      if (isTyping) return;

      e.preventDefault();
      removePlantInstance(selectedPlantId);
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [removePlantInstance, selectedPlantId]);

  return (
    <div>
      <div className="garden-board-toolbar d-flex flex-wrap align-items-center justify-content-between gap-2">
        <div className="small text-muted">
          <strong>Scale:</strong> 1 square = {CELL_SIZE_CM}cm x {CELL_SIZE_CM}cm
        </div>

        <div className="d-flex align-items-center gap-2">
          <span className="small text-muted">Zoom: {Math.round(zoom * 100)}%</span>
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={zoomOut}>
            -
          </button>
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={resetZoom}>
            Reset
          </button>
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={zoomIn}>
            +
          </button>
        </div>
      </div>

      <div
        ref={boardRef}
        className="garden-board"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div
          className="garden-board-inner"
          style={{
            width: "100%",
            minWidth: `${bounds.cols * scaledCellSize}px`,
            height: `${Math.max(bounds.rows * scaledCellSize, 760)}px`,
            backgroundImage: `
              linear-gradient(to right, rgba(31,42,36,0.12) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(31,42,36,0.12) 1px, transparent 1px)
            `,
            backgroundSize: `${scaledCellSize}px ${scaledCellSize}px`,
          }}
        >
          {boxes.map((box) => (
            <div
              key={box.id}
              onMouseDown={(e) => handleMouseDownBox(e, box)}
              className="garden-box"
              style={{
                position: "absolute",
                left: box.x * scaledCellSize,
                top: box.y * scaledCellSize,
                width: box.w * scaledCellSize,
                height: box.h * scaledCellSize,
                border:
                  box.id === selectedBoxId
                    ? "3px solid #3467a6"
                    : "2px solid #7d624e",
                boxSizing: "border-box",
                cursor: draggingBoxId === box.id ? "grabbing" : "move",
                zIndex: 2,
              }}
            >
              <div
                onMouseDown={(e) => handleMouseDownResize(e, box)}
                style={{
                  position: "absolute",
                  right: -7,
                  bottom: -7,
                  width: 14,
                  height: 14,
                  borderRadius: "8px",
                  background: "#3467a6",
                  border: "2px solid white",
                  cursor: "nwse-resize",
                  boxShadow: "0 0 0 1px rgba(0,0,0,0.15)",
                }}
              />
            </div>
          ))}

          {absolutePlantInstances.map((plant) => {
            const isWeedPatch = plant.kind === "weed";
            const isWeedControl = plant.kind === "weed_control";
            const widthPx = plant.width * scaledCellSize;
            const heightPx = plant.height * scaledCellSize;
            const seedSize = Math.max(
              10,
              Math.min(22, Math.round(Math.min(widthPx, heightPx) * 0.2))
            );
            const tileBackground = plant.locked
              ? "rgba(255,194,62,0.35)"
              : isWeedPatch
                ? "rgba(143,45,45,0.2)"
                : isWeedControl
                  ? "rgba(52,103,166,0.2)"
                  : "rgba(47,111,78,0.22)";
            const tileBorder = plant.locked
              ? "3px solid #d9a616"
              : isWeedPatch
                ? "2px solid rgba(143,45,45,0.78)"
                : isWeedControl
                  ? "2px solid rgba(52,103,166,0.78)"
                  : "2px solid rgba(47,111,78,0.72)";
            const seedBackground = isWeedPatch
              ? "rgba(117,33,33,0.86)"
              : isWeedControl
                ? "rgba(36,79,131,0.86)"
                : "rgba(70,45,20,0.85)";
            const statusLabel = plant.locked
              ? "Locked"
              : isWeedPatch
                ? "Weed"
                : isWeedControl
                  ? "Control"
                  : "";

            return (
              <div
                key={plant.id}
                onMouseDown={(e) => handleMouseDownPlant(e, plant)}
                onClick={(e) => {
                  e.stopPropagation();
                  if (dragMovedRef.current) {
                    dragMovedRef.current = false;
                    return;
                  }
                  setSelectedPlantId(plant.id);
                  togglePlantLocked(plant.id);
                }}
                onContextMenu={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  removePlantInstance(plant.id);
                }}
                title={`${plant.name}${plant.locked ? " (locked)" : ""}${isWeedControl && plant.controlsWeed ? ` - controls ${plant.controlsWeed}` : ""} - left click lock/unlock and select for delete, right click remove`}
                style={{
                  position: "absolute",
                  left: plant.col * scaledCellSize,
                  top: plant.row * scaledCellSize,
                  width: widthPx,
                  height: heightPx,
                  background: tileBackground,
                  border: tileBorder,
                  outline: selectedPlantId === plant.id ? "3px solid #3467a6" : "none",
                  outlineOffset: "2px",
                  borderRadius: "6px",
                  boxSizing: "border-box",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  zIndex: 4,
                  cursor: draggingPlantId === plant.id ? "grabbing" : "grab",
                  overflow: "hidden",
                  userSelect: "none",
                }}
              >
                <div
                  className="plant-tile-label"
                  style={{
                    width: seedSize,
                    height: seedSize,
                    borderRadius: "50%",
                    background: seedBackground,
                    border: "2px solid rgba(255,255,255,0.9)",
                    boxShadow: "0 1px 4px rgba(0,0,0,0.2)",
                  }}
                />

                <div
                  style={{
                    position: "absolute",
                    left: 0,
                    right: 0,
                    top: "28%",
                    transform: "translateY(-50%)",
                    width: "100%",
                    textAlign: "center",
                    fontSize: `${Math.max(
                      12,
                      Math.min(32, Math.round(Math.min(widthPx, heightPx) * 0.2))
                    )}px`,
                    padding: "0 6px",
                    boxSizing: "border-box",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {shortLabel(plant.name)}
                </div>

                {statusLabel && (
                  <div
                    className="locked-pill"
                    style={{
                      position: "absolute",
                      top: 4,
                      right: 4,
                      fontSize: "12px",
                      padding: "1px 6px",
                      lineHeight: 1.2,
                    }}
                  >
                    {statusLabel}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="d-flex flex-wrap align-items-center gap-2 mt-2">
        {selectedPlant ? (
          <small className="text-muted">
            Last clicked plant: <strong>{selectedPlant.name}</strong>
            {selectedPlant.locked ? " (locked)" : " (unlocked)"}
          </small>
        ) : (
          <small className="text-muted">Click a plant to lock/unlock it, then use Delete/Backspace if needed.</small>
        )}

        <button
          type="button"
          className="btn btn-sm btn-outline-danger"
          onClick={deleteSelectedPlant}
          disabled={!selectedPlant}
        >
          Delete {itemLabel}
        </button>
      </div>

      <div className="small text-muted mt-2">
        {boardTip || (
          <>
            Tip: drag a plant from the list into a box or use + to add one. Left click a plant to
            lock/unlock it and make it the active plant for delete. Press <strong>Delete</strong> or <strong>Backspace</strong> to remove the active plant. Right click a plant to remove it. Hold <strong>Ctrl</strong> and use the mouse wheel to zoom.
            You can drag plants between boxes as long as the new box has room.
          </>
        )}
      </div>
    </div>
  );
}

export default GardenGrid;
