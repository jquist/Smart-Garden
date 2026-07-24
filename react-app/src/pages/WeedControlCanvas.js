import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import BoxesPanel from "../components/canvas/BoxesPanel";
import GardenGrid from "../components/canvas/GardenGrid";
import PlantBadges from "../components/PlantBadges";
import {
  makeBox,
  makePlantInstance,
  findFirstFitForPlant,
  placedPlantCollidesUsingBoxes,
  withAbsolutePlantPosition,
} from "../components/canvas/canvasUtils";
import { API } from "../constants";

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

function getUniqueWeedNames(instances) {
  return Array.from(
    new Set(
      instances
        .filter((plant) => plant.kind === "weed")
        .map((plant) => plant.name)
    )
  ).sort((a, b) => a.localeCompare(b));
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

function WeedPickerModal({
  weeds,
  selectedWeedIds,
  setSelectedWeedIds,
  loading,
  error,
  onContinue,
  onClose,
}) {
  const [search, setSearch] = useState("");

  const filteredWeeds = useMemo(() => {
    return weeds
      .filter((weed) => plantMatchesSearch(weed, search))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [weeds, search]);

  function toggleWeed(weedId) {
    setSelectedWeedIds((prev) => {
      const next = new Set(prev);
      if (next.has(weedId)) next.delete(weedId);
      else next.add(weedId);
      return next;
    });
  }

  return (
    <ModalShell
      kicker="Weed control"
      title="What weeds do you have?"
      wide
      onClose={onClose}
      footer={
        <>
          <span className="small text-muted">
            {selectedWeedIds.size} weed{selectedWeedIds.size === 1 ? "" : "s"} selected
          </span>
          <button
            type="button"
            className="btn btn-success"
            disabled={selectedWeedIds.size === 0 || loading}
            onClick={onContinue}
          >
            Next
          </button>
        </>
      }
    >
      <input
        type="text"
        className="form-control mb-3"
        placeholder="Search weeds..."
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />

      {loading && <p>Loading weeds...</p>}
      {error && <p>Could not load weed data.</p>}

      <div className="weed-picker-list">
        {filteredWeeds.map((weed) => (
          <label key={weed.id} className="weed-check-row">
            <input
              type="checkbox"
              checked={selectedWeedIds.has(weed.id)}
              onChange={() => toggleWeed(weed.id)}
            />
            <span>
              <strong>{weed.name}</strong>
              {weed.weed_management_notes && (
                <small>{weed.weed_management_notes}</small>
              )}
            </span>
          </label>
        ))}
      </div>
    </ModalShell>
  );
}

function WeedMappingPanel({
  selectedWeeds,
  plantInstances,
  onAddWeed,
  onRemoveWeed,
  onChangeWeeds,
  onReviewControls,
}) {
  const countsById = useMemo(
    () => countByPlantId(plantInstances, "weed"),
    [plantInstances]
  );

  function handleDragStart(event, weed) {
    event.dataTransfer.setData(
      "application/json",
      JSON.stringify({
        source: "weed-panel",
        plantId: weed.id,
        name: weed.name,
        kind: "weed",
      })
    );
    event.dataTransfer.effectAllowed = "copy";
  }

  return (
    <div className="card p-3 mb-3 weed-workflow-card">
      <h5 className="mb-2">Weeds on this plan</h5>
      <p className="small text-muted">
        Drag each weed into the bed where it appears, or use + to add another patch.
      </p>

      <div className="weed-control-legend mb-3">
        <span><i className="legend-swatch legend-swatch-weed" /> Weed patch</span>
        <span><i className="legend-swatch legend-swatch-control" /> Control plant</span>
      </div>

      <div className="weed-panel-list">
        {selectedWeeds.map((weed) => {
          const count = countsById[weed.id] || 0;

          return (
            <div
              key={weed.id}
              className={`panel-section p-2 mb-2 ${count > 0 ? "border-danger bg-light" : ""}`}
              draggable
              onDragStart={(event) => handleDragStart(event, weed)}
            >
              <div className="d-flex justify-content-between align-items-center gap-2">
                <div>
                  <strong>{weed.name}</strong>
                  <div className="small text-muted">Patches: {count}</div>
                </div>

                <div className="d-flex align-items-center gap-2">
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => onRemoveWeed(weed)}
                    disabled={count === 0}
                  >
                    -
                  </button>
                  <span style={{ minWidth: "24px", textAlign: "center" }}>{count}</span>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => onAddWeed(weed)}
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <button
        type="button"
        className="btn btn-success w-100 mt-2"
        onClick={onReviewControls}
        disabled={getUniqueWeedNames(plantInstances).length === 0}
      >
        Done placing weeds
      </button>
      <button
        type="button"
        className="btn btn-outline-secondary w-100 mt-2"
        onClick={onChangeWeeds}
      >
        {selectedWeeds.length === 0 ? "Add weed modifier" : "Change weed list"}
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

function WeedResultPanel({ controlInstances, placementMessage, selectedByWeed, onReviewControls }) {
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
      <h5 className="mb-2">Control plan</h5>
      {placementMessage && (
        <div className="alert alert-info py-2 small mb-3">
          {placementMessage}
        </div>
      )}

      {controlInstances.length === 0 ? (
        <small className="text-muted">No control plants have been added yet.</small>
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
        Review weed controls
      </button>
    </div>
  );
}

function WeedControlCanvas() {
  const [boxes, setBoxes] = useState([makeBox("square", 0)]);
  const [selectedBoxId, setSelectedBoxId] = useState(null);
  const [plantInstances, setPlantInstances] = useState([]);
  const [selectedWeedIds, setSelectedWeedIds] = useState(() => new Set());
  const [showWeedPicker, setShowWeedPicker] = useState(true);
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

  const selectedWeeds = useMemo(
    () => weeds.filter((weed) => selectedWeedIds.has(weed.id)),
    [weeds, selectedWeedIds]
  );

  const weedNamesOnCanvas = useMemo(
    () => getUniqueWeedNames(plantInstances),
    [plantInstances]
  );

  const controlInstances = useMemo(
    () => plantInstances.filter((plant) => plant.kind === "weed_control"),
    [plantInstances]
  );

  function createWeedInstance(weed, boxIndex = 0, localRow = 0, localCol = 0) {
    return {
      ...makePlantInstance(weed, boxIndex, localRow, localCol),
      kind: "weed",
    };
  }

  function createControlInstance(plant, weedName, boxIndex = 0, localRow = 0, localCol = 0) {
    return {
      ...makePlantInstance(plant, boxIndex, localRow, localCol),
      kind: "weed_control",
      controlsWeed: weedName,
    };
  }

  function placeWeedInList(currentPlants, weed) {
    const newWeed = createWeedInstance(weed);
    const fit = findFirstFitForPlant(newWeed, boxes, currentPlants, plantsData, false);
    if (!fit) return null;

    return {
      ...newWeed,
      boxIndex: fit.boxIndex,
      localRow: fit.localRow,
      localCol: fit.localCol,
    };
  }

  function handleStartMapping() {
    const selectedIdSet = new Set(selectedWeedIds);

    setPlantInstances((prev) => {
      const next = prev.filter(
        (plant) => plant.kind === "weed" && selectedIdSet.has(plant.plantId)
      );

      for (const weed of selectedWeeds) {
        const alreadyPlaced = next.some((plant) => plant.plantId === weed.id);
        if (alreadyPlaced) continue;

        const placedWeed = placeWeedInList(next, weed);
        if (placedWeed) next.push(placedWeed);
      }

      return next;
    });

    setPlacementMessage("");
    setShowWeedPicker(false);
  }

  function handleAddWeed(weed) {
    let placed = false;

    setPlantInstances((prev) => {
      const placedWeed = placeWeedInList(prev, weed);
      if (!placedWeed) return prev;
      placed = true;
      return [...prev, placedWeed];
    });

    setTimeout(() => {
      if (!placed) alert("No space found in the current boxes for that weed patch.");
    }, 0);
  }

  function handleRemoveWeed(weed) {
    setPlantInstances((prev) => {
      const lastIndex = [...prev]
        .reverse()
        .findIndex((instance) => instance.kind === "weed" && instance.plantId === weed.id);

      if (lastIndex === -1) return prev;

      const actualIndex = prev.length - 1 - lastIndex;
      const next = [...prev];
      next.splice(actualIndex, 1);
      return next;
    });
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
    const names = getUniqueWeedNames(plantInstances);
    if (names.length === 0) {
      alert("Place at least one weed patch first.");
      return;
    }

    setRecommendationStepIndex(0);
    setShowRecommendations(true);
  }

  function handleApplyControls() {
    const notPlaced = [];
    let placedCount = 0;
    const nextPlants = plantInstances.filter((plant) => plant.kind !== "weed_control");

    for (const weedName of weedNamesOnCanvas) {
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
        ? "No control plants were added. Choose at least one plant in the recommendation pop-up."
        : `Added ${placedCount} weed-control plant${placedCount === 1 ? "" : "s"} to the canvas.${failedText}`
    );
    setShowRecommendations(false);
  }

  return (
    <div className="canvas-page weed-control-page">
      <header className="page-header">
        <div>
          <p className="page-kicker">Weed control canvas</p>
          <h1 className="page-title">Map weeds, then place plants that suppress them.</h1>
          <p className="page-subtitle">
            This planner is only for weed-control planting. Pick the weeds you have, place their patches, then choose suppressor plants for each weed.
          </p>
        </div>
        <div className="selected-count">
          {weedNamesOnCanvas.length} weed type{weedNamesOnCanvas.length === 1 ? "" : "s"} mapped
        </div>
      </header>

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
            acceptedDropSources={["weed-panel"]}
            itemLabel="item"
            boardTip={
              <>
                Tip: drag weed patches from the weed list into a bed, then press <strong>Done placing weeds</strong>. The final blue tiles are the weed-control plants you picked in the recommendation steps.
              </>
            }
          />
        </div>

        <aside className="planner-sidebar">
          <BoxesPanel
            boxes={boxes}
            setBoxes={setBoxes}
            selectedBoxId={selectedBoxId}
            setSelectedBoxId={setSelectedBoxId}
            onRemoveSelected={handleRemoveSelectedBox}
            onClearSelected={handleClearSelectedBox}
          />

          <WeedMappingPanel
            selectedWeeds={selectedWeeds}
            plantInstances={plantInstances}
            onAddWeed={handleAddWeed}
            onRemoveWeed={handleRemoveWeed}
            onChangeWeeds={() => setShowWeedPicker(true)}
            onReviewControls={handleReviewControls}
          />

          <WeedResultPanel
            controlInstances={controlInstances}
            placementMessage={placementMessage}
            selectedByWeed={selectedByWeed}
            onReviewControls={handleReviewControls}
          />
        </aside>
      </div>

      {showWeedPicker && (
        <WeedPickerModal
          weeds={weeds}
          selectedWeedIds={selectedWeedIds}
          setSelectedWeedIds={setSelectedWeedIds}
          loading={isPending}
          error={error}
          onContinue={handleStartMapping}
          onClose={() => setShowWeedPicker(false)}
        />
      )}

      {showRecommendations && (
        <WeedRecommendationModal
          weedNames={weedNamesOnCanvas}
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
