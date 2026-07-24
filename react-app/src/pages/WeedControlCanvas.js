import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import BoxesPanel from "../components/canvas/BoxesPanel";
import GardenGrid from "../components/canvas/GardenGrid";
import SavedPlansPanel from "../components/canvas/SavedPlansPanel";
import PlantBadges from "../components/PlantBadges";
import {
  CELL_CM,
  makeBox,
  makePlantInstance,
  placedPlantCollidesUsingBoxes,
  withAbsolutePlantPosition,
} from "../components/canvas/canvasUtils";
import { API } from "../constants";

const WEED_STEPS = [
  { key: "layout", label: "Layout" },
  { key: "weeds", label: "Weeds" },
  { key: "map", label: "Map" },
  { key: "controls", label: "Controls" },
];

const WEED_PATCH_SIZE_OPTIONS = [
  { value: "small", label: "Small patch", width: 1, height: 1 },
  { value: "medium", label: "Medium patch", width: 2, height: 2 },
  { value: "large", label: "Large patch", width: 3, height: 3 },
];

function normaliseName(name) {
  return String(name || "").trim().toLowerCase();
}

function listHasName(list, name) {
  const key = normaliseName(name);
  return Array.isArray(list) && list.some((item) => normaliseName(item) === key);
}

function isWeedPlant(plant) {
  return plant?.plant_category === "weed" || listHasName(plant?.plant_roles, "weed");
}

function plantMatchesSearch(plant, query) {
  const q = query.trim().toLowerCase();
  if (!q) return true;

  return (
    String(plant.name || "").toLowerCase().includes(q) ||
    String(plant.weed_management_notes || "").toLowerCase().includes(q) ||
    (plant.plant_roles || []).some((role) => String(role).toLowerCase().includes(q))
  );
}

function getPlantByName(plantsData, name) {
  const key = normaliseName(name);
  return plantsData.find((plant) => normaliseName(plant.name) === key);
}

function getPatchSizeOption(value) {
  return (
    WEED_PATCH_SIZE_OPTIONS.find((option) => option.value === value) ||
    WEED_PATCH_SIZE_OPTIONS[0]
  );
}

function sanitisePatchAmount(amount) {
  return Math.max(1, Math.min(99, Number(amount) || 1));
}

function getPlanAmount(plan) {
  return sanitisePatchAmount(plan?.amount);
}

function getPlanAreaText(plan) {
  const amount = getPlanAmount(plan);
  const patch = getPatchSizeOption(plan?.size);
  const cells = amount * patch.width * patch.height;
  const squareMeters = (cells * CELL_CM * CELL_CM) / 10000;
  const rounded = squareMeters >= 1 ? squareMeters.toFixed(1) : squareMeters.toFixed(2);

  return `${cells} grid square${cells === 1 ? "" : "s"} (${rounded} m2 rough coverage)`;
}

function getSuppressorCandidates(weed, plantsData) {
  if (!weed) return [];

  const names = new Map();

  for (const name of weed.weed_suppressors || []) {
    names.set(normaliseName(name), name);
  }

  for (const plant of plantsData) {
    if (plant.plant_category === "weed") continue;
    if (listHasName(plant.weeds_suppressed, weed.name)) {
      names.set(normaliseName(plant.name), plant.name);
    }
  }

  return Array.from(names.values())
    .map((name) => getPlantByName(plantsData, name))
    .filter(Boolean)
    .filter((plant) => plant.plant_category !== "weed")
    .sort((a, b) => {
      const aRole = listHasName(a.plant_roles, "weed_suppressor") ? 0 : 1;
      const bRole = listHasName(b.plant_roles, "weed_suppressor") ? 0 : 1;
      if (aRole !== bRole) return aRole - bRole;
      return a.name.localeCompare(b.name);
    });
}

function countByPlantId(instances, kind) {
  const counts = {};

  for (const instance of instances) {
    if (kind && instance.kind !== kind) continue;
    counts[instance.plantId] = (counts[instance.plantId] || 0) + 1;
  }

  return counts;
}

function ModalShell({ kicker, title, children, footer, wide = false, onClose }) {
  return (
    <div className="workflow-modal-backdrop" role="dialog" aria-modal="true">
      <div className={`workflow-modal ${wide ? "workflow-modal-wide" : ""}`}>
        <div className="workflow-modal-header">
          <div className="workflow-modal-title">
            {kicker && <p className="page-kicker">{kicker}</p>}
            <h2>{title}</h2>
          </div>
          {onClose && (
            <button
              type="button"
              className="workflow-modal-close"
              onClick={onClose}
              aria-label="Close pop-up"
            >
              X
            </button>
          )}
        </div>
        <div className="workflow-modal-body">{children}</div>
        {footer && <div className="workflow-modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

function WeedStepNav({ activeStep, setActiveStep, canOpenMap, canOpenControls }) {
  function canOpenStep(index) {
    if (index <= 1) return true;
    if (index === 2) return canOpenMap;
    return canOpenControls;
  }

  return (
    <div className="weed-stepper" aria-label="Weed control steps">
      {WEED_STEPS.map((step, index) => (
        <button
          key={step.key}
          type="button"
          className={`weed-step-button ${activeStep === index ? "weed-step-button-active" : ""} ${activeStep > index ? "weed-step-button-done" : ""}`}
          onClick={() => canOpenStep(index) && setActiveStep(index)}
          disabled={!canOpenStep(index)}
        >
          <span>{index + 1}</span>
          {step.label}
        </button>
      ))}
    </div>
  );
}

function WeedLayerTogglePanel({
  showWeeds,
  setShowWeeds,
  showControlPlants,
  setShowControlPlants,
  weedPatchCount,
  controlPlantCount,
}) {
  return (
    <div className="card p-3 mb-3 weed-workflow-card">
      <h5 className="mb-2">Visual layers</h5>
      <div className="d-grid gap-2">
        <label className="form-check form-switch weed-layer-toggle">
          <input
            className="form-check-input"
            type="checkbox"
            checked={showWeeds}
            onChange={(event) => setShowWeeds(event.target.checked)}
          />
          <span className="form-check-label">Weed patches ({weedPatchCount})</span>
        </label>
        <label className="form-check form-switch weed-layer-toggle">
          <input
            className="form-check-input"
            type="checkbox"
            checked={showControlPlants}
            onChange={(event) => setShowControlPlants(event.target.checked)}
          />
          <span className="form-check-label">Suppressor plants ({controlPlantCount})</span>
        </label>
      </div>
    </div>
  );
}

function WeedSelectionPanel({
  weeds,
  weedPlans,
  loading,
  error,
  onAddWeedPlan,
  onRemoveWeedPlan,
  onSetWeedAmount,
  onSetWeedSize,
  onNext,
}) {
  const [search, setSearch] = useState("");

  const filteredWeeds = useMemo(() => {
    return weeds
      .filter((weed) => plantMatchesSearch(weed, search))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [weeds, search]);

  const selectedCount = Object.keys(weedPlans).length;
  const plannedPatchCount = Object.values(weedPlans).reduce(
    (total, plan) => total + getPlanAmount(plan),
    0
  );

  return (
    <div className="card p-3 mb-3 weed-workflow-card">
      <h5 className="mb-2">Select weeds</h5>
      <div className="selected-count mb-3">
        {selectedCount} weed type{selectedCount === 1 ? "" : "s"}, {plannedPatchCount} patch{plannedPatchCount === 1 ? "" : "es"}
      </div>

      <input
        type="text"
        className="form-control mb-3"
        placeholder="Search weeds..."
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />

      {loading && <p>Loading weeds...</p>}
      {error && <p>Could not load weed data.</p>}

      <div className="weed-picker-list weed-plan-list">
        {filteredWeeds.map((weed) => {
          const plan = weedPlans[weed.id];
          const selected = Boolean(plan);

          return (
            <div
              key={weed.id}
              className={`weed-plan-row ${selected ? "weed-plan-row-selected" : ""}`}
            >
              <label className="weed-plan-check">
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={(event) =>
                    event.target.checked ? onAddWeedPlan(weed) : onRemoveWeedPlan(weed)
                  }
                />
                <span>
                  <strong>{weed.name}</strong>
                  {weed.weed_management_notes && <small>{weed.weed_management_notes}</small>}
                </span>
              </label>

              {selected && (
                <div className="weed-plan-controls">
                  <label>
                    <span>Amount</span>
                    <input
                      type="number"
                      className="form-control"
                      min="1"
                      max="99"
                      value={getPlanAmount(plan)}
                      onChange={(event) => onSetWeedAmount(weed, event.target.value)}
                    />
                  </label>

                  <label>
                    <span>Patch size</span>
                    <select
                      className="form-select"
                      value={plan.size}
                      onChange={(event) => onSetWeedSize(weed, event.target.value)}
                    >
                      {WEED_PATCH_SIZE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <small className="text-muted">{getPlanAreaText(plan)}</small>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <button
        type="button"
        className="btn btn-success w-100 mt-3"
        onClick={onNext}
        disabled={selectedCount === 0}
      >
        Next: map weeds
      </button>
    </div>
  );
}

function WeedMappingPanel({
  plannedWeeds,
  plantInstances,
  onBackToWeeds,
  onReviewControls,
  canReviewControls,
}) {
  const countsById = useMemo(
    () => countByPlantId(plantInstances, "weed"),
    [plantInstances]
  );

  const remainingTotal = plannedWeeds.reduce((total, weed) => {
    const planned = getPlanAmount(weed.weedPlan);
    const placed = countsById[weed.id] || 0;
    return total + Math.max(planned - placed, 0);
  }, 0);

  function handleDragStart(event, weed) {
    const placed = countsById[weed.id] || 0;
    const planned = getPlanAmount(weed.weedPlan);
    if (placed >= planned) {
      event.preventDefault();
      return;
    }

    const patch = getPatchSizeOption(weed.weedPlan?.size);

    event.dataTransfer.setData(
      "application/json",
      JSON.stringify({
        source: "weed-panel",
        plantId: weed.id,
        name: weed.name,
        kind: "weed",
        width: patch.width,
        height: patch.height,
        sizeSame: Math.min(patch.width, patch.height),
      })
    );
    event.dataTransfer.effectAllowed = "copy";
  }

  return (
    <div className="card p-3 mb-3 weed-workflow-card">
      <h5 className="mb-2">Map weed patches</h5>
      <div className="weed-control-legend mb-3">
        <span><i className="legend-swatch legend-swatch-weed" /> Weed patch</span>
        <span><i className="legend-swatch legend-swatch-control" /> Suppressor plant</span>
      </div>

      <div className="weed-panel-list">
        {plannedWeeds.map((weed) => {
          const planned = getPlanAmount(weed.weedPlan);
          const placed = countsById[weed.id] || 0;
          const remaining = Math.max(planned - placed, 0);
          const patch = getPatchSizeOption(weed.weedPlan?.size);

          return (
            <div
              key={weed.id}
              className={`panel-section p-2 mb-2 ${remaining === 0 ? "weed-plan-complete" : ""}`}
              draggable={remaining > 0}
              onDragStart={(event) => handleDragStart(event, weed)}
            >
              <div className="d-flex justify-content-between align-items-start gap-2">
                <div>
                  <strong>{weed.name}</strong>
                  <div className="small text-muted">
                    Placed {placed} of {planned}
                  </div>
                  <div className="small text-muted">
                    {patch.label}: {patch.width} x {patch.height} grid
                  </div>
                </div>
                <span className={`weed-remaining-pill ${remaining === 0 ? "weed-remaining-pill-done" : ""}`}>
                  {remaining} left
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <button
        type="button"
        className="btn btn-success w-100 mt-2"
        onClick={onReviewControls}
        disabled={!canReviewControls}
      >
        Choose suppressor plants
      </button>
      {remainingTotal > 0 && (
        <small className="text-muted d-block mt-2">
          {remainingTotal} planned weed patch{remainingTotal === 1 ? "" : "es"} still need placing.
        </small>
      )}
      <button
        type="button"
        className="btn btn-outline-secondary w-100 mt-2"
        onClick={onBackToWeeds}
      >
        Change weed list
      </button>
    </div>
  );
}

function WeedRecommendationModal({
  weedNames,
  plantsData,
  selectedByWeed,
  setSelectedByWeed,
  stepIndex,
  setStepIndex,
  onClose,
  onFinish,
}) {
  const weedName = weedNames[stepIndex];
  const weed = getPlantByName(plantsData, weedName);
  const candidates = useMemo(
    () => getSuppressorCandidates(weed, plantsData),
    [weed, plantsData]
  );
  const selectedForWeed = selectedByWeed[weedName] || new Set();
  const isLast = stepIndex >= weedNames.length - 1;

  function toggleSuppressor(plantName) {
    setSelectedByWeed((prev) => {
      const current = new Set(prev[weedName] || []);
      if (current.has(plantName)) current.delete(plantName);
      else current.add(plantName);
      return { ...prev, [weedName]: current };
    });
  }

  function goNext() {
    if (isLast) {
      onFinish();
      return;
    }
    setStepIndex((prev) => prev + 1);
  }

  return (
    <ModalShell
      kicker={`Weed ${stepIndex + 1} of ${weedNames.length}`}
      title={`Plants that can help with ${weedName}`}
      wide
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn btn-outline-secondary" onClick={onClose}>
            Back to canvas
          </button>
          <div className="d-flex gap-2">
            <button
              type="button"
              className="btn btn-outline-secondary"
              disabled={stepIndex === 0}
              onClick={() => setStepIndex((prev) => Math.max(0, prev - 1))}
            >
              Back
            </button>
            <button type="button" className="btn btn-success" onClick={goNext}>
              {isLast ? "Done" : "Next"}
            </button>
          </div>
        </>
      }
    >
      {weed?.weed_management_notes && (
        <div className="alert alert-warning py-2 small mb-3">
          {weed.weed_management_notes}
        </div>
      )}

      {candidates.length === 0 ? (
        <div className="empty-state">
          No suppressor plants are listed for this weed yet.
        </div>
      ) : (
        <div className="weed-recommendation-list">
          {candidates.map((plant) => (
            <label key={plant.id} className="weed-recommendation-row">
              <input
                type="checkbox"
                checked={selectedForWeed.has(plant.name)}
                onChange={() => toggleSuppressor(plant.name)}
              />
              <span className="weed-recommendation-main">
                <strong>{plant.name}</strong>
                <PlantBadges plant={plant} maxRoles={2} />
                {plant.weeds_suppressed?.length > 0 && (
                  <small>
                    Helps with: {plant.weeds_suppressed.slice(0, 4).join(", ")}
                    {plant.weeds_suppressed.length > 4 ? "..." : ""}
                  </small>
                )}
              </span>
            </label>
          ))}
        </div>
      )}
    </ModalShell>
  );
}

function WeedResultPanel({
  controlInstances,
  placementMessage,
  selectedByWeed,
  onReviewControls,
  onBackToMap,
}) {
  const selectedPairs = Object.entries(selectedByWeed)
    .flatMap(([weedName, names]) =>
      Array.from(names || []).map((plantName) => ({ weedName, plantName }))
    )
    .sort((a, b) => a.weedName.localeCompare(b.weedName) || a.plantName.localeCompare(b.plantName));

  const controlsByName = controlInstances.reduce((counts, plant) => {
    counts[plant.name] = (counts[plant.name] || 0) + 1;
    return counts;
  }, {});

  return (
    <div className="card p-3 mb-3 weed-workflow-card">
      <h5 className="mb-2">Suppressor plan</h5>
      {placementMessage && (
        <div className="alert alert-info py-2 small mb-3">
          {placementMessage}
        </div>
      )}

      {controlInstances.length === 0 ? (
        <small className="text-muted">No suppressor plants have been added yet.</small>
      ) : (
        <div className="d-grid gap-2 mb-3">
          {Object.entries(controlsByName)
            .sort((a, b) => a[0].localeCompare(b[0]))
            .map(([name, count]) => (
              <div key={name} className="panel-section p-2 d-flex justify-content-between gap-2">
                <strong>{name}</strong>
                <span className="small text-muted">x {count}</span>
              </div>
            ))}
        </div>
      )}

      {selectedPairs.length > 0 && (
        <div className="weed-selected-pairs">
          {selectedPairs.map((pair) => (
            <div key={`${pair.weedName}-${pair.plantName}`}>
              <strong>{pair.weedName}</strong>
              <span>{pair.plantName}</span>
            </div>
          ))}
        </div>
      )}

      <button
        type="button"
        className="btn btn-outline-success w-100 mt-3"
        onClick={onReviewControls}
      >
        Review suppressor choices
      </button>
      <button
        type="button"
        className="btn btn-outline-secondary w-100 mt-2"
        onClick={onBackToMap}
      >
        Back to weed map
      </button>
    </div>
  );
}

function WeedControlCanvas() {
  const [searchParams] = useSearchParams();
  const initialPlanId = searchParams.get("plan") || "";
  const [boxes, setBoxes] = useState([makeBox("square", 0)]);
  const [selectedBoxId, setSelectedBoxId] = useState(null);
  const [plantInstances, setPlantInstances] = useState([]);
  const [weedPlans, setWeedPlans] = useState({});
  const [activeStep, setActiveStep] = useState(0);
  const [showWeeds, setShowWeeds] = useState(true);
  const [showControlPlants, setShowControlPlants] = useState(true);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [recommendationStepIndex, setRecommendationStepIndex] = useState(0);
  const [selectedByWeed, setSelectedByWeed] = useState({});
  const [placementMessage, setPlacementMessage] = useState("");

  const { data: plantsData = [], isPending, error } = useQuery({
    queryKey: ["weedControlPlants"],
    queryFn: async () => {
      const response = await fetch(`${API}plant/`);
      if (!response.ok) {
        throw new Error("Failed to load plants");
      }
      return response.json();
    },
  });

  const weeds = useMemo(
    () => plantsData.filter(isWeedPlant).sort((a, b) => a.name.localeCompare(b.name)),
    [plantsData]
  );

  const plannedWeeds = useMemo(
    () =>
      weeds
        .filter((weed) => weedPlans[weed.id])
        .map((weed) => ({ ...weed, weedPlan: weedPlans[weed.id] })),
    [weeds, weedPlans]
  );

  const plannedWeedNames = useMemo(
    () => plannedWeeds.map((weed) => weed.name),
    [plannedWeeds]
  );

  const weedPatchCountsById = useMemo(
    () => countByPlantId(plantInstances, "weed"),
    [plantInstances]
  );

  const weedPatchCount = useMemo(
    () => plantInstances.filter((plant) => plant.kind === "weed").length,
    [plantInstances]
  );

  const controlInstances = useMemo(
    () => plantInstances.filter((plant) => plant.kind === "weed_control"),
    [plantInstances]
  );

  const plannedPatchCount = useMemo(
    () =>
      plannedWeeds.reduce(
        (total, weed) => total + getPlanAmount(weed.weedPlan),
        0
      ),
    [plannedWeeds]
  );

  const allPlannedPatchesMapped =
    plannedPatchCount > 0 &&
    plannedWeeds.every((weed) => (weedPatchCountsById[weed.id] || 0) >= getPlanAmount(weed.weedPlan));

  const hiddenPlantKinds = [
    showWeeds ? null : "weed",
    showControlPlants ? null : "weed_control",
  ].filter(Boolean);

  const savedSelectedByWeed = useMemo(
    () =>
      Object.fromEntries(
        Object.entries(selectedByWeed).map(([weedName, names]) => [
          weedName,
          Array.from(names || []),
        ])
      ),
    [selectedByWeed]
  );

  function addWeedPlan(weed) {
    setWeedPlans((prev) => ({
      ...prev,
      [weed.id]: prev[weed.id] || {
        weedId: weed.id,
        amount: 1,
        size: "small",
      },
    }));
  }

  function removeWeedPlan(weed) {
    setWeedPlans((prev) => {
      const next = { ...prev };
      delete next[weed.id];
      return next;
    });
    setPlantInstances((prev) =>
      prev.filter(
        (plant) =>
          !(plant.kind === "weed" && plant.plantId === weed.id) &&
          !(plant.kind === "weed_control" && normaliseName(plant.controlsWeed) === normaliseName(weed.name))
      )
    );
    setSelectedByWeed((prev) => {
      const next = { ...prev };
      delete next[weed.name];
      return next;
    });
    setPlacementMessage("");
  }

  function trimWeedInstancesToAmount(instances, weed, amount) {
    let seen = 0;

    return instances.filter((plant) => {
      if (plant.kind !== "weed" || plant.plantId !== weed.id) return true;
      seen += 1;
      return seen <= amount;
    });
  }

  function setWeedAmount(weed, amountRaw) {
    const amount = sanitisePatchAmount(amountRaw);
    setWeedPlans((prev) => ({
      ...prev,
      [weed.id]: {
        ...(prev[weed.id] || { weedId: weed.id, size: "small" }),
        amount,
      },
    }));
    setPlantInstances((prev) =>
      trimWeedInstancesToAmount(prev, weed, amount).filter(
        (plant) =>
          !(plant.kind === "weed_control" && normaliseName(plant.controlsWeed) === normaliseName(weed.name))
      )
    );
    setPlacementMessage("");
  }

  function setWeedSize(weed, size) {
    setWeedPlans((prev) => ({
      ...prev,
      [weed.id]: {
        ...(prev[weed.id] || { weedId: weed.id, amount: 1 }),
        size,
      },
    }));
    setPlantInstances((prev) =>
      prev.filter(
        (plant) =>
          !(plant.kind === "weed_control" && normaliseName(plant.controlsWeed) === normaliseName(weed.name))
      )
    );
    setPlacementMessage("");
  }

  function handleRemoveSelectedBox() {
    if (!selectedBoxId) return;
    const removedIndex = boxes.findIndex((box) => box.id === selectedBoxId);
    if (removedIndex === -1) return;

    setBoxes((prev) => prev.filter((box) => box.id !== selectedBoxId));
    setPlantInstances((prev) =>
      prev
        .filter((plant) => plant.boxIndex !== removedIndex)
        .map((plant) => (plant.boxIndex > removedIndex ? { ...plant, boxIndex: plant.boxIndex - 1 } : plant))
    );
    setSelectedBoxId(null);
  }

  function handleClearSelectedBox() {
    if (!selectedBoxId) return;
    const selectedIndex = boxes.findIndex((box) => box.id === selectedBoxId);
    if (selectedIndex === -1) return;

    setPlantInstances((prev) =>
      prev.filter((plant) => plant.boxIndex !== selectedIndex)
    );
  }

  function handleLoadSavedPlan(plan) {
    setBoxes(Array.isArray(plan.boxes) && plan.boxes.length > 0 ? plan.boxes : [makeBox("square", 0)]);
    setPlantInstances(Array.isArray(plan.plant_instances) ? plan.plant_instances : []);
    setWeedPlans(plan.metadata?.weedPlans || {});
    setSelectedByWeed(
      Object.fromEntries(
        Object.entries(plan.metadata?.selectedByWeed || {}).map(([weedName, names]) => [
          weedName,
          new Set(Array.isArray(names) ? names : []),
        ])
      )
    );
    setPlacementMessage(plan.metadata?.placementMessage || "");
    setActiveStep(Math.max(0, Math.min(3, Number(plan.metadata?.activeStep ?? 0))));
  }

  function createControlInstance(plant, weedName, boxIndex = 0, localRow = 0, localCol = 0) {
    return {
      ...makePlantInstance(plant, boxIndex, localRow, localCol),
      kind: "weed_control",
      controlsWeed: weedName,
    };
  }

  function getDistanceToWeed(candidate, weedName, currentPlants) {
    const targetWeeds = currentPlants
      .filter(
        (plant) =>
          plant.kind === "weed" &&
          normaliseName(plant.name) === normaliseName(weedName)
      )
      .map((plant) => withAbsolutePlantPosition(plant, boxes));

    if (targetWeeds.length === 0) return 0;

    const absolute = withAbsolutePlantPosition(candidate, boxes);
    const candidateCenter = {
      row: absolute.row + absolute.height / 2,
      col: absolute.col + absolute.width / 2,
    };

    return Math.min(
      ...targetWeeds.map((weed) => {
        const weedCenter = {
          row: weed.row + weed.height / 2,
          col: weed.col + weed.width / 2,
        };

        const boxPenalty = weed.boxIndex === candidate.boxIndex ? 0 : 6;
        return (
          Math.abs(candidateCenter.row - weedCenter.row) +
          Math.abs(candidateCenter.col - weedCenter.col) +
          boxPenalty
        );
      })
    );
  }

  function placeControlNearWeed(currentPlants, plant, weedName) {
    const baseControl = createControlInstance(plant, weedName);
    const candidates = [];

    for (let boxIndex = 0; boxIndex < boxes.length; boxIndex++) {
      const box = boxes[boxIndex];
      if (!box || baseControl.width > box.w || baseControl.height > box.h) continue;

      for (let localRow = 0; localRow <= box.h - baseControl.height; localRow++) {
        for (let localCol = 0; localCol <= box.w - baseControl.width; localCol++) {
          const candidate = {
            ...baseControl,
            boxIndex,
            localRow,
            localCol,
          };

          if (placedPlantCollidesUsingBoxes(candidate, currentPlants, boxes, null, plantsData)) {
            continue;
          }

          candidates.push({
            plant: candidate,
            score: getDistanceToWeed(candidate, weedName, currentPlants),
          });
        }
      }
    }

    candidates.sort((a, b) => a.score - b.score);
    return candidates[0]?.plant || null;
  }

  function handleReviewControls() {
    if (plannedWeeds.length === 0) {
      alert("Select at least one weed first.");
      return;
    }

    if (!allPlannedPatchesMapped) {
      alert("Place every planned weed patch on the canvas first.");
      return;
    }

    setRecommendationStepIndex(0);
    setShowRecommendations(true);
  }

  function handleApplyControls() {
    const notPlaced = [];
    let placedCount = 0;
    const nextPlants = plantInstances.filter((plant) => plant.kind !== "weed_control");

    for (const weedName of plannedWeedNames) {
      const selectedNames = Array.from(selectedByWeed[weedName] || []);

      for (const plantName of selectedNames) {
        const plant = getPlantByName(plantsData, plantName);
        if (!plant) {
          notPlaced.push(`${plantName} for ${weedName}`);
          continue;
        }

        const placedControl = placeControlNearWeed(nextPlants, plant, weedName);
        if (!placedControl) {
          notPlaced.push(`${plantName} for ${weedName}`);
          continue;
        }

        nextPlants.push(placedControl);
        placedCount += 1;
      }
    }

    setPlantInstances(nextPlants);

    const failedText = notPlaced.length > 0
      ? ` Could not fit: ${notPlaced.join(", ")}.`
      : "";
    setPlacementMessage(
      placedCount === 0
        ? "No suppressor plants were added. Choose at least one plant in the recommendation pop-up."
        : `Added ${placedCount} suppressor plant${placedCount === 1 ? "" : "s"} to the canvas.${failedText}`
    );
    setShowRecommendations(false);
    setActiveStep(3);
  }

  function getBoardTip() {
    if (activeStep === 0) {
      return "Step 1: shape the garden beds first. Use the box controls on the right to add, clear, or remove beds.";
    }
    if (activeStep === 1) {
      return "Step 2: select weeds and set rough patch amount and size. Nothing is placed until the mapping step.";
    }
    if (activeStep === 2) {
      return "Step 3: drag planned weed patches from the right onto the matching places in the garden.";
    }
    return "Step 4: suppressor plants are shown near the weed patches they were chosen for.";
  }

  return (
    <div className="canvas-page weed-control-page">
      <header className="page-header">
        <div>
          <p className="page-kicker">Weed control canvas</p>
          <h1 className="page-title">Plan weeds first, then place suppressor plants.</h1>
          <p className="page-subtitle">
            Build the garden layout, estimate the weed patches, map them onto the beds, then choose plants that help suppress those weeds.
          </p>
        </div>
        <div className="selected-count">
          {weedPatchCount} of {plannedPatchCount} weed patch{plannedPatchCount === 1 ? "" : "es"} mapped
        </div>
      </header>

      <WeedStepNav
        activeStep={activeStep}
        setActiveStep={setActiveStep}
        canOpenMap={plannedWeeds.length > 0}
        canOpenControls={controlInstances.length > 0 || allPlannedPatchesMapped}
      />

      <div className="planner-layout">
        <div className="garden-panel">
          <GardenGrid
            boxes={boxes}
            setBoxes={setBoxes}
            selectedBoxId={selectedBoxId}
            setSelectedBoxId={setSelectedBoxId}
            sortResult={null}
            plantInstances={plantInstances}
            setPlantInstances={setPlantInstances}
            plantsData={plantsData}
            acceptedDropSources={activeStep === 2 ? ["weed-panel"] : []}
            hiddenPlantKinds={hiddenPlantKinds}
            itemLabel="item"
            boardTip={getBoardTip()}
          />
        </div>

        <aside className="planner-sidebar">
          <WeedLayerTogglePanel
            showWeeds={showWeeds}
            setShowWeeds={setShowWeeds}
            showControlPlants={showControlPlants}
            setShowControlPlants={setShowControlPlants}
            weedPatchCount={weedPatchCount}
            controlPlantCount={controlInstances.length}
          />

          <SavedPlansPanel
            planType="weed"
            boxes={boxes}
            plantInstances={plantInstances}
            metadata={{
              weedPlans,
              selectedByWeed: savedSelectedByWeed,
              placementMessage,
              activeStep,
            }}
            initialPlanId={initialPlanId}
            onLoadPlan={handleLoadSavedPlan}
          />

          {activeStep === 0 && (
            <>
              <BoxesPanel
                boxes={boxes}
                setBoxes={setBoxes}
                selectedBoxId={selectedBoxId}
                setSelectedBoxId={setSelectedBoxId}
                onRemoveSelected={handleRemoveSelectedBox}
                onClearSelected={handleClearSelectedBox}
              />
              <button
                type="button"
                className="btn btn-success w-100 mb-3"
                onClick={() => setActiveStep(1)}
              >
                Next: select weeds
              </button>
            </>
          )}

          {activeStep === 1 && (
            <WeedSelectionPanel
              weeds={weeds}
              weedPlans={weedPlans}
              loading={isPending}
              error={error}
              onAddWeedPlan={addWeedPlan}
              onRemoveWeedPlan={removeWeedPlan}
              onSetWeedAmount={setWeedAmount}
              onSetWeedSize={setWeedSize}
              onNext={() => setActiveStep(2)}
            />
          )}

          {activeStep === 2 && (
            <WeedMappingPanel
              plannedWeeds={plannedWeeds}
              plantInstances={plantInstances}
              onBackToWeeds={() => setActiveStep(1)}
              onReviewControls={handleReviewControls}
              canReviewControls={allPlannedPatchesMapped}
            />
          )}

          {activeStep === 3 && (
            <WeedResultPanel
              controlInstances={controlInstances}
              placementMessage={placementMessage}
              selectedByWeed={selectedByWeed}
              onReviewControls={handleReviewControls}
              onBackToMap={() => setActiveStep(2)}
            />
          )}
        </aside>
      </div>

      {showRecommendations && (
        <WeedRecommendationModal
          weedNames={plannedWeedNames}
          plantsData={plantsData}
          selectedByWeed={selectedByWeed}
          setSelectedByWeed={setSelectedByWeed}
          stepIndex={recommendationStepIndex}
          setStepIndex={setRecommendationStepIndex}
          onClose={() => setShowRecommendations(false)}
          onFinish={handleApplyControls}
        />
      )}
    </div>
  );
}

export default WeedControlCanvas;
