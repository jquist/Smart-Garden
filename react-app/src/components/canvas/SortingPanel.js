import React, { useState } from "react";

function SortingPanel({
  sortOptions,
  setSortOptions,
  onSort,
  onForceStop,
  isSorting,
  progressPercent = 0,
  progressLabel = "",
  estimatedTimeText = "",
}) {
  const [open, setOpen] = useState(true);
  const isLongSort =
    sortOptions.algorithm === "backtracking" ||
    sortOptions.algorithm === "constraint";

  return (
    <div className="card p-3 mb-3">
      <button
        type="button"
        className="btn btn-link panel-toggle text-decoration-none p-0 d-flex justify-content-between align-items-center w-100"
        onClick={() => setOpen((prev) => !prev)}
      >
        <h5 className="mb-0">Sorting</h5>
        <span>{open ? "Hide" : "Show"}</span>
      </button>

      {open && (
        <>

      <div className="mb-3">
        <label className="form-label">Algorithm</label>
        <select
          className="form-select"
          value={sortOptions.algorithm}
          onChange={(e) =>
            setSortOptions((prev) => ({
              ...prev,
              algorithm: e.target.value,
            }))
          }
          disabled={isSorting}
        >
          <option value="quick">Quick</option>
          <option value="backtracking">Medium</option>
          <option value="constraint">Slow</option>
        </select>
      </div>

      <div className="form-check form-switch mb-2">
        <input
          className="form-check-input"
          type="checkbox"
          checked={sortOptions.avoidSpacing}
          disabled={isSorting}
          onChange={(e) =>
            setSortOptions((prev) => ({
              ...prev,
              avoidSpacing: e.target.checked,
            }))
          }
        />
        <label className="form-check-label">Extra space for avoid</label>
      </div>

      <div className="form-check form-switch mb-2">
        <input
          className="form-check-input"
          type="checkbox"
          checked={sortOptions.forceSameTogether}
          disabled={isSorting}
          onChange={(e) =>
            setSortOptions((prev) => ({
              ...prev,
              forceSameTogether: e.target.checked,
              forceRow: e.target.checked ? prev.forceRow : false,
              forceColumn: e.target.checked ? prev.forceColumn : false,
            }))
          }
        />
        <label className="form-check-label">Force same plants together</label>
      </div>

      <div className="form-check form-switch mb-2">
        <input
          className="form-check-input"
          type="checkbox"
          checked={sortOptions.forceRow}
          disabled={isSorting || !sortOptions.forceSameTogether}
          onChange={(e) =>
            setSortOptions((prev) => ({
              ...prev,
              forceRow: e.target.checked,
              forceColumn: e.target.checked ? false : prev.forceColumn,
            }))
          }
        />
        <label className="form-check-label">Force row</label>
      </div>

      <div className="form-check form-switch mb-2">
        <input
          className="form-check-input"
          type="checkbox"
          checked={sortOptions.forceColumn}
          disabled={isSorting || !sortOptions.forceSameTogether}
          onChange={(e) =>
            setSortOptions((prev) => ({
              ...prev,
              forceColumn: e.target.checked,
              forceRow: e.target.checked ? false : prev.forceRow,
            }))
          }
        />
        <label className="form-check-label">Force column</label>
      </div>

      <div className="form-check form-switch mb-2">
        <input
          className="form-check-input"
          type="checkbox"
          checked={sortOptions.maxSpread}
          disabled={isSorting}
          onChange={(e) =>
            setSortOptions((prev) => ({
              ...prev,
              maxSpread: e.target.checked,
            }))
          }
        />
        <label className="form-check-label">Max spread</label>
      </div>

      <div className="form-check form-switch mb-2">
        <input
          className="form-check-input"
          type="checkbox"
          checked={!!sortOptions.noCompanionOverlap}
          disabled={isSorting}
          onChange={(e) =>
            setSortOptions((prev) => ({
              ...prev,
              noCompanionOverlap: e.target.checked,
            }))
          }
        />
        <label className="form-check-label">No companion overlap</label>
        <small className="text-muted d-block ms-5">
          Stops different plant types sharing the same cell, even if they are companions.
        </small>
      </div>

      <div className="form-check form-switch mb-1">
        <input
          className="form-check-input"
          type="checkbox"
          checked={sortOptions.maximiseSearch}
          disabled={isSorting || sortOptions.algorithm !== "constraint"}
          onChange={(e) =>
            setSortOptions((prev) => ({
              ...prev,
              maximiseSearch: e.target.checked,
            }))
          }
        />
        <label className="form-check-label">Optimal search</label>
        <small className="text-muted d-block ms-5 mb-3">
          Recommended for larger boxes with lots of empty space - helps grouping and spacing behave as expected.
        </small>
      </div>

      {!isSorting ? (
        <button
          className="btn btn-success w-100"
          onClick={onSort}
        >
          Auto Sort
        </button>
      ) : (
        <button
          className="btn btn-danger w-100"
          onClick={onForceStop}
        >
          Force stop autosort
        </button>
      )}

      {isSorting && (isLongSort || sortOptions.maxSpread || sortOptions.maximiseSearch) && (
        <div className="mt-3">
          <div className="d-flex justify-content-between mb-1">
            <small>{progressLabel || "Working..."}</small>
            <small>{progressPercent}%</small>
          </div>

          <div
            className="progress"
            role="progressbar"
            aria-valuenow={progressPercent}
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <div
              className="progress-bar progress-bar-striped progress-bar-animated"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <small className="text-muted d-block mt-2">
            {estimatedTimeText || "This may take a little while for larger layouts."}
          </small>
        </div>
      )}
          </>
      )}
    </div>
  );
}

export default SortingPanel;
