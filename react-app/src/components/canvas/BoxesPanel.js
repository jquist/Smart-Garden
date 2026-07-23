import React, { useState } from "react";
import { makeBox } from "./canvasUtils";

function BoxesPanel({
  boxes,
  setBoxes,
  selectedBoxId,
  setSelectedBoxId,
  onRemoveSelected,
  onClearSelected,
}) {
  const [open, setOpen] = useState(true);
  const selectedBox = boxes.find((b) => b.id === selectedBoxId) || null;

  function addSquare() {
    const newBox = makeBox("square", boxes.length);
    setBoxes((prev) => [...prev, newBox]);
    setSelectedBoxId(newBox.id);
  }

  function addRectangle() {
    const newBox = makeBox("rectangle", boxes.length);
    setBoxes((prev) => [...prev, newBox]);
    setSelectedBoxId(newBox.id);
  }

  function clearSelected() {
    if (!selectedBoxId) return;
    onClearSelected?.();
  }

  function removeSelected() {
    if (!selectedBoxId) return;
    onRemoveSelected?.();
  }

  function updateSelected(changes) {
    if (!selectedBoxId) return;
    setBoxes((prev) =>
      prev.map((box) =>
        box.id === selectedBoxId ? { ...box, ...changes } : box
      )
    );
  }

  function nudge(dx, dy) {
    if (!selectedBox) return;
    updateSelected({
      x: Math.max(0, selectedBox.x + dx),
      y: Math.max(0, selectedBox.y + dy),
    });
  }

  function resize(dw, dh) {
    if (!selectedBox) return;
    updateSelected({
      w: Math.max(1, selectedBox.w + dw),
      h: Math.max(1, selectedBox.h + dh),
    });
  }

  return (
    <div className="card p-3 mb-3">
      <button
        type="button"
        className="btn btn-link panel-toggle text-decoration-none p-0 d-flex justify-content-between align-items-center w-100"
        onClick={() => setOpen((prev) => !prev)}
      >
        <h5 className="mb-0">Boxes</h5>
        <span>{open ? "Hide" : "Show"}</span>
      </button>

      {!open && (
        <small className="text-muted mt-2">
          {boxes.length} box{boxes.length === 1 ? "" : "es"} on board
        </small>
      )}

      {open && (
        <>
          <div className="d-grid gap-2 my-3">
            <button className="btn btn-outline-primary" onClick={addSquare}>
              Add square
            </button>
            <button className="btn btn-outline-primary" onClick={addRectangle}>
              Add rectangle
            </button>
            <button
              className="btn btn-outline-warning"
              onClick={clearSelected}
              disabled={!selectedBoxId}
            >
              Clear selected box
            </button>
            <button
              className="btn btn-outline-danger"
              onClick={removeSelected}
              disabled={!selectedBoxId}
            >
              Remove selected box
            </button>
          </div>

          {selectedBox && (
            <div className="panel-section p-2 mb-3">
              <div className="mb-2">
                <strong>Selected:</strong> {selectedBox.type}
              </div>

              <div className="mb-2 small text-muted">
                x: {selectedBox.x}, y: {selectedBox.y}, w: {selectedBox.w}, h: {selectedBox.h}
              </div>

              <div className="d-flex gap-2 flex-wrap mb-2">
                <button className="btn btn-sm btn-outline-secondary" onClick={() => nudge(0, -1)}>Up</button>
                <button className="btn btn-sm btn-outline-secondary" onClick={() => nudge(0, 1)}>Down</button>
                <button className="btn btn-sm btn-outline-secondary" onClick={() => nudge(-1, 0)}>Left</button>
                <button className="btn btn-sm btn-outline-secondary" onClick={() => nudge(1, 0)}>Right</button>
              </div>

              <div className="d-flex gap-2 flex-wrap">
                <button className="btn btn-sm btn-outline-secondary" onClick={() => resize(1, 0)}>W +</button>
                <button className="btn btn-sm btn-outline-secondary" onClick={() => resize(-1, 0)}>W -</button>
                <button className="btn btn-sm btn-outline-secondary" onClick={() => resize(0, 1)}>H +</button>
                <button className="btn btn-sm btn-outline-secondary" onClick={() => resize(0, -1)}>H -</button>
              </div>
            </div>
          )}

          <small className="text-muted">
            {boxes.length} box{boxes.length === 1 ? "" : "es"} on board
          </small>
        </>
      )}
    </div>
  );
}

export default BoxesPanel;
