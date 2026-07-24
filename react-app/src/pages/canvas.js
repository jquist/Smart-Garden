import React, { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import BoxesPanel from "../components/canvas/BoxesPanel";
import GardenGrid from "../components/canvas/GardenGrid";
import PlantsPanel from "../components/canvas/PlantsPanel";
import SavedPlansPanel from "../components/canvas/SavedPlansPanel";
import SortingPanel from "../components/canvas/SortingPanel";
import {
  makeBox,
  boxesToSolverPayload,
  buildLockedPlantsPayload,
  buildAutosortPlantsPayload,
  CELL_CM,
  makePlantInstance,
  findFirstFitForPlant,
  getPlantTypeColour,
  normalisePlantTypeName,
} from "../components/canvas/canvasUtils";
import { API } from "../constants";
import CRpanel from "../components/canvas/CompRecPanel";

function getResolvedAlgorithm(baseAlgorithm, maxSpread) {
  if (baseAlgorithm === "quick") return maxSpread ? "quick_fill" : "quick";
  if (baseAlgorithm === "backtracking") return maxSpread ? "backtracking_minmax" : "backtracking_k";
  if (baseAlgorithm === "constraint") return maxSpread ? "constraint_fill" : "constraint";
  return "quick";
}

function estimateSolveSeconds(baseAlgorithm, maxSpread, maximiseSearch, boxes, plantInstances) {
  const plantCount = plantInstances.length;
  const usableCells = boxes.reduce((total, box) => total + box.w * box.h, 0);
  const optionMultiplier = (maxSpread ? 1.4 : 1) * (maximiseSearch ? 3 : 1);

  if (baseAlgorithm === "quick") {
    return Math.max(1, Math.ceil((plantCount + usableCells / 40) * 0.15 * optionMultiplier));
  }

  if (baseAlgorithm === "backtracking") {
    return Math.max(3, Math.ceil((plantCount * 0.8 + usableCells / 18) * optionMultiplier));
  }

  return Math.max(6, Math.ceil((plantCount * usableCells * 0.035 + plantCount ** 2 * 0.12) * optionMultiplier));
}

function getProgressText(baseAlgorithm, maxSpread, maximiseSearch, boxes, plantInstances) {
  const spreadText = maxSpread ? " with max spread" : "";
  const searchText = maximiseSearch ? " using maximise search" : "";
  const seconds = estimateSolveSeconds(baseAlgorithm, maxSpread, maximiseSearch, boxes, plantInstances);
  const eta = seconds < 60
    ? `Rough estimate: about ${seconds} seconds. This is only an estimate.`
    : `Rough estimate: about ${Math.ceil(seconds / 60)} minutes. This is only an estimate and depends on the Garden design.`;

  if (baseAlgorithm === "quick") {
    return { label: `Running quick solver${spreadText}${searchText}...`, eta };
  }
  if (baseAlgorithm === "backtracking") {
    return { label: `Running medium solver${spreadText}${searchText}...`, eta };
  }
  return { label: `Running slow solver${spreadText}${searchText}...`, eta };
}

function FreeMoveCanvas() {
  const [searchParams] = useSearchParams();
  const initialPlanId = searchParams.get("plan") || "";
  const [boxes, setBoxes] = useState([makeBox("square", 0)]);
  const [selectedBoxId, setSelectedBoxId] = useState(null);
  const [plantsData, setPlantsData] = useState([]);
  const [plantInstances, setPlantInstances] = useState([]);

  const [sortOptions, setSortOptions] = useState({
    algorithm: "quick",
    avoidSpacing: true,
    forceSameTogether: false,
    forceRow: false,
    forceColumn: false,
    maxSpread: false,
    noCompanionOverlap: false,
    maximiseSearch: false,
  });

  const [sortResult, setSortResult] = useState(null);
  const [isSorting, setIsSorting] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressLabel, setProgressLabel] = useState("");
  const [estimatedTimeText, setEstimatedTimeText] = useState("");
  const [fillMessage, setFillMessage] = useState("");
  const [selectedPlantsOpen, setSelectedPlantsOpen] = useState(true);
  const [focusedPlantName, setFocusedPlantName] = useState("");

  const progressTimerRef = useRef(null);
  const abortControllerRef = useRef(null);
  const skipClearSortResultRef = useRef(false);
  const preSortPlantInstancesRef = useRef([]);

  const countsByName = useMemo(() => {
    const counts = {};
    for (const plant of plantInstances) counts[plant.name] = (counts[plant.name] || 0) + 1;
    return counts;
  }, [plantInstances]);

  const plantSummary = useMemo(() => {
    return Object.entries(countsByName)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([name, count]) => ({ name, count }));
  }, [countsByName]);

  const fillablePlantSummary = useMemo(() => {
    const counts = {};

    for (const plant of plantInstances) {
      if (plant.locked) continue;
      counts[plant.name] = (counts[plant.name] || 0) + 1;
    }

    return Object.entries(counts)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([name, count]) => ({ name, count }));
  }, [plantInstances]);

  const notPlacedSummary = useMemo(() => {
    const names = sortResult?.not_placed || [];
    const counts = {};

    for (const name of names) {
      counts[name] = (counts[name] || 0) + 1;
    }

    return Object.entries(counts)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([name, count]) => ({ name, count }));
  }, [sortResult]);

  useEffect(() => {
    if (focusedPlantName && !countsByName[focusedPlantName]) {
      setFocusedPlantName("");
    }
  }, [countsByName, focusedPlantName]);

  function toggleFocusedPlantName(name) {
    setFocusedPlantName((prev) =>
      normalisePlantTypeName(prev) === normalisePlantTypeName(name) ? "" : name
    );
  }

  function handlePlantSummaryKeyDown(event, name) {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    toggleFocusedPlantName(name);
  }

  function placeOnePlantInList(currentPlants, plantData, options = {}) {
    if (!plantData || boxes.length === 0) return null;

    const newPlant = makePlantInstance(plantData, 0, 0, 0);
    const fit = findFirstFitForPlant(
      newPlant,
      boxes,
      currentPlants,
      plantsData,
      !!options.preferCompanionOverlap
    );

    if (!fit) return null;

    return {
      ...newPlant,
      boxIndex: fit.boxIndex,
      localRow: fit.localRow,
      localCol: fit.localCol,
    };
  }

  function getPlantArea(plantData) {
    const probe = makePlantInstance(plantData, 0, 0, 0);
    return Math.max(1, probe.width * probe.height);
  }

  useEffect(() => {
    if (skipClearSortResultRef.current) {
      skipClearSortResultRef.current = false;
      return;
    }

    setSortResult(null);
  }, [plantInstances]);

  useEffect(() => {
    return () => {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, []);

  function startProgress(optionsOverride = null, plantsOverride = null) {
    const effectiveOptions = optionsOverride || sortOptions;
    const effectivePlants = plantsOverride || plantInstances;

    const { label, eta } = getProgressText(
      effectiveOptions.algorithm,
      effectiveOptions.maxSpread,
      effectiveOptions.maximiseSearch,
      boxes,
      effectivePlants
    );

    const estimatedSeconds = estimateSolveSeconds(
      effectiveOptions.algorithm,
      effectiveOptions.maxSpread,
      effectiveOptions.maximiseSearch,
      boxes,
      effectivePlants
    );

    const startedAt = Date.now();
    const estimatedMs = Math.max(1000, estimatedSeconds * 1000);

    setProgressPercent(0);
    setProgressLabel(label);
    setEstimatedTimeText(eta);

    if (progressTimerRef.current) clearInterval(progressTimerRef.current);

    progressTimerRef.current = setInterval(() => {
      const elapsedMs = Date.now() - startedAt;
      const percent = Math.min(90, Math.floor((elapsedMs / estimatedMs) * 90));

      setProgressPercent(percent);
    }, 200);
  }

  function stopProgress() {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }

  function resetSortingUi(label = "") {
    stopProgress();
    setIsSorting(false);
    setProgressPercent(0);
    setProgressLabel(label);
    setEstimatedTimeText("");
  }

  function handleForceStop() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    resetSortingUi("Autosort stopped");
  }

  async function runSortWithOptions(optionsOverride = {}, plantsOverride = null, savePreSort = true) {
    const effectiveOptions = {
      ...sortOptions,
      ...optionsOverride,
    };

    const effectivePlants = plantsOverride || plantInstances;

    try {
      if (savePreSort) {
        preSortPlantInstancesRef.current = effectivePlants.map((plant) => ({ ...plant }));
      }

      setIsSorting(true);
      startProgress(effectiveOptions, effectivePlants);

      const controller = new AbortController();
      abortControllerRef.current = controller;

      const resolvedAlgorithm = getResolvedAlgorithm(
        effectiveOptions.algorithm,
        effectiveOptions.maxSpread
      );

      const payload = {
        algorithm: resolvedAlgorithm,
        boxes: boxesToSolverPayload(boxes),
        plants: buildAutosortPlantsPayload(effectivePlants),
        locked_plants: buildLockedPlantsPayload(effectivePlants, boxes),
        next_to: effectiveOptions.forceSameTogether,
        avoid: effectiveOptions.avoidSpacing,
        fill: effectiveOptions.maxSpread,
        force_row: effectiveOptions.forceRow,
        force_column: effectiveOptions.forceColumn,
        maximise_search: effectiveOptions.maximiseSearch,
        no_companion_overlap: effectiveOptions.noCompanionOverlap,
        k:
          effectiveOptions.forceRow || effectiveOptions.forceColumn
            ? 2
            : resolvedAlgorithm === "backtracking_minmax"
              ? 6
              : 3,
        cell_cm: CELL_CM,
        time_limit:
          effectiveOptions.maximiseSearch && effectiveOptions.algorithm === "constraint"
            ? 120
            : 12,
      };

      const response = await fetch(`${API}auto-sort/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data?.error || "Autosort failed");

      const requestedPlantCount = effectivePlants.filter((p) => !p.locked).length;
      const returnedPlantCount = Array.isArray(data.plant_instances)
        ? data.plant_instances.length
        : 0;

      if (requestedPlantCount > 0 && returnedPlantCount === 0) {
        throw new Error(
          "Autosort failed: the solver returned no placements, so the canvas was kept unchanged. Try turning off 'force same plants together' or test with fewer plants while this solver issue is fixed."
        );
      }

      const hydratedPlants = (data.plant_instances || []).map((plant, index) => {
        const plantData = plantsData.find((p) => p.name === plant.name);
        return {
          id: `sorted_${Date.now()}_${index}_${Math.random().toString(16).slice(2)}`,
          plantId: plantData?.id ?? `sorted_${plant.name}_${index}`,
          name: plant.name,
          boxIndex: plant.box_index,
          localRow: plant.row,
          localCol: plant.col,
          width: plant.width,
          height: plant.height,
          sizeSame: plant.size_same ?? plant.width,
          locked: !!plant.locked,
        };
      });

      abortControllerRef.current = null;
      stopProgress();
      setProgressPercent(100);
      setProgressLabel("Done");

      if (hydratedPlants.length > 0) {
        skipClearSortResultRef.current = true;
        setPlantInstances(hydratedPlants);
      }

      setSortResult(data);

      setTimeout(() => resetSortingUi(""), 250);
    } catch (error) {
      abortControllerRef.current = null;
      stopProgress();

      if (error.name === "AbortError") {
        resetSortingUi("Autosort stopped");
        return;
      }

      console.error(error);
      resetSortingUi("");
      alert(error.message || "Autosort failed");
    }
  }

  async function handleSort() {
    await runSortWithOptions({}, null, true);
  }

  async function handleQuickMinSpaceResort() {
    const originalPlants = preSortPlantInstancesRef.current;

    if (!originalPlants || originalPlants.length === 0) {
      alert("Could not find the plant list from before the sort.");
      return;
    }

    const quickMinOptions = {
      algorithm: "quick",
      maxSpread: false,
      forceSameTogether: false,
      forceRow: false,
      forceColumn: false,
      maximiseSearch: false,
      // keep avoidSpacing as it currently is, so avoid rules still behave consistently
      avoidSpacing: sortOptions.avoidSpacing,
    };

    setSortOptions((prev) => ({
      ...prev,
      ...quickMinOptions,
    }));

    await runSortWithOptions(
      quickMinOptions,
      originalPlants.map((plant) => ({ ...plant })),
      false
    );
  }

  function handleAddPlant(plant, options = {}) {
    if (!boxes.length) {
      alert("Add a box first.");
      return;
    }

    let placed = false;

    setPlantInstances((prev) => {
      const placedPlant = placeOnePlantInList(prev, plant, options);
      if (!placedPlant) return prev;

      placed = true;
      return [...prev, placedPlant];
    });

    setTimeout(() => {
      if (!placed) {
        alert("No space found in the current boxes for that plant.");
      }
    }, 0);
  }

  function handleEqualFillSelectedTypes() {
    if (!boxes.length) {
      alert("Add a box first.");
      return;
    }

    const selectedTypes = fillablePlantSummary
      .map((item) => plantsData.find((plant) => plant.name === item.name))
      .filter(Boolean);

    if (selectedTypes.length === 0) {
      alert("Add at least one unlocked plant type first.");
      return;
    }

    const areaByName = {};
    for (const plant of selectedTypes) {
      areaByName[plant.name] = getPlantArea(plant);
    }

    let addedCount = 0;
    let addedByName = {};

    setPlantInstances((prev) => {
      const next = prev.map((plant) => ({ ...plant }));
      const maxExtraAttempts =
        boxes.reduce((total, box) => total + box.w * box.h, 0) * selectedTypes.length + 50;
      let attempts = 0;

      while (attempts < maxExtraAttempts) {
        attempts += 1;

        const currentAreaByName = {};
        const currentCountByName = {};

        for (const plant of next) {
          if (plant.locked) continue;

          currentAreaByName[plant.name] =
            (currentAreaByName[plant.name] || 0) + Math.max(1, plant.width * plant.height);
          currentCountByName[plant.name] = (currentCountByName[plant.name] || 0) + 1;
        }

        const candidates = selectedTypes
          .map((plant) => ({
            plant,
            currentArea: currentAreaByName[plant.name] || 0,
            currentCount: currentCountByName[plant.name] || 0,
          }))
          .sort((a, b) => {
            if (a.currentArea !== b.currentArea) return a.currentArea - b.currentArea;
            if (a.currentCount !== b.currentCount) return a.currentCount - b.currentCount;
            return areaByName[b.plant.name] - areaByName[a.plant.name];
          });

        let placedThisRound = false;

        for (const candidate of candidates) {
          const placedPlant = placeOnePlantInList(next, candidate.plant, {
            preferCompanionOverlap: !sortOptions.noCompanionOverlap,
          });

          if (!placedPlant) continue;

          next.push(placedPlant);
          addedCount += 1;
          addedByName[placedPlant.name] = (addedByName[placedPlant.name] || 0) + 1;
          placedThisRound = true;
          break;
        }

        if (!placedThisRound) break;
      }

      return addedCount > 0 ? next : prev;
    });

    setTimeout(() => {
      if (addedCount === 0) {
        const message = "No extra plants could fit with the current boxes and companion/spacing rules.";
        setFillMessage(message);
        alert(message);
        return;
      }

      const details = Object.entries(addedByName)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([name, count]) => `${name} x ${count}`)
        .join(", ");

      setFillMessage(
        `Added ${addedCount} plant${addedCount === 1 ? "" : "s"}: ${details}. If you do not like the layout, try Auto Sort.`
      );
    }, 0);
  }

  function normalisePlantName(name) {
    return String(name || "").trim().toLowerCase();
  }

  function getPlantDataByName(name) {
    const key = normalisePlantName(name);
    return plantsData.find((plant) => normalisePlantName(plant.name) === key);
  }

  function listHasPlantName(list, name) {
    const key = normalisePlantName(name);
    return Array.isArray(list) && list.some((item) => normalisePlantName(item) === key);
  }

  function relationScoreByName(nameA, nameB) {
    if (normalisePlantName(nameA) === normalisePlantName(nameB)) return 0;

    const plantA = getPlantDataByName(nameA);
    const plantB = getPlantDataByName(nameB);
    if (!plantA || !plantB) return 0;

    const aAvoidsB = listHasPlantName(plantA.plants_avoid_names, plantB.name);
    const bAvoidsA = listHasPlantName(plantB.plants_avoid_names, plantA.name);
    if (aAvoidsB || bAvoidsA) return -1000;

    const aHelpsB =
      listHasPlantName(plantA.companion_helps_names, plantB.name) ||
      listHasPlantName(plantB.companion_helped_by_names, plantA.name);

    const bHelpsA =
      listHasPlantName(plantB.companion_helps_names, plantA.name) ||
      listHasPlantName(plantA.companion_helped_by_names, plantB.name);

    if (aHelpsB && bHelpsA) return 2;
    if (aHelpsB || bHelpsA) return 1;
    return 0;
  }

  function countCompanionFitForCurrentGrid(plantName, maxChecks = 80) {
    const plantData = getPlantDataByName(plantName);
    if (!plantData || !boxes.length) return 0;

    const nextPlants = plantInstances.map((plant) => ({ ...plant }));
    let count = 0;

    for (let attempt = 0; attempt < maxChecks; attempt++) {
      const placedPlant = placeOnePlantInList(nextPlants, plantData, {
        preferCompanionOverlap: !sortOptions.noCompanionOverlap,
      });

      if (!placedPlant) break;
      nextPlants.push(placedPlant);
      count += 1;
    }

    return count;
  }

  function candidatePlacementScore(placedPlant, existingPlants) {
    let score = Math.max(1, placedPlant.width * placedPlant.height);

    for (const existing of existingPlants) {
      const relation = relationScoreByName(placedPlant.name, existing.name);
      if (relation > 0) score += relation * 100;
    }

    return score;
  }

  function chooseNextCompanionPlacement(currentPlants, selectedPlantData, mode) {
    let best = null;
    let bestScore = -Infinity;

    for (const plantData of selectedPlantData) {
      const placedPlant = placeOnePlantInList(currentPlants, plantData, {
        preferCompanionOverlap: !sortOptions.noCompanionOverlap,
      });

      if (!placedPlant) continue;

      let score = candidatePlacementScore(placedPlant, currentPlants);
      if (mode === "maximise") score += Math.max(1, placedPlant.width * placedPlant.height) * 10;
      if (mode === "smart") score += Math.max(1, placedPlant.width * placedPlant.height) * 3;

      if (score > bestScore) {
        bestScore = score;
        best = placedPlant;
      }
    }

    return best;
  }

  function handleCompanionFill(selectedNames, placementMode = "best") {
    const names = Array.from(selectedNames || []);

    if (!boxes.length) {
      alert("Add a box first.");
      return;
    }

    if (names.length === 0) {
      alert("Select at least one recommendation first.");
      return;
    }

    const selectedPlantData = names
      .map((name) => getPlantDataByName(name))
      .filter(Boolean);

    if (selectedPlantData.length === 0) {
      alert("Could not find the selected recommendation plants in the loaded plant data.");
      return;
    }

    let addedCount = 0;
    const addedByName = {};

    setPlantInstances((prev) => {
      const next = prev.map((plant) => ({ ...plant }));
      const maxSteps = placementMode === "best"
        ? selectedPlantData.length
        : boxes.reduce((total, box) => total + box.w * box.h, 0) + selectedPlantData.length;

      for (let step = 0; step < maxSteps; step++) {
        const placedPlant = chooseNextCompanionPlacement(next, selectedPlantData, placementMode);
        if (!placedPlant) break;

        next.push(placedPlant);
        addedCount += 1;
        addedByName[placedPlant.name] = (addedByName[placedPlant.name] || 0) + 1;

        if (placementMode === "best" && addedCount >= selectedPlantData.length) break;
      }

      return addedCount > 0 ? next : prev;
    });

    setTimeout(() => {
      if (addedCount === 0) {
        alert("No useful companion gap was found for the selected recommendations.");
        return;
      }

      const details = Object.entries(addedByName)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([name, count]) => `${name} x ${count}`)
        .join(", ");

      setFillMessage(`Companion fill added ${addedCount} plant${addedCount === 1 ? "" : "s"}: ${details}.`);
    }, 0);
  }


  function handleRemovePlant(plant) {
    setPlantInstances((prev) => {
      const lastIndex = [...prev].reverse().findIndex((instance) => instance.plantId === plant.id);
      if (lastIndex === -1) return prev;
      const actualIndex = prev.length - 1 - lastIndex;
      const next = [...prev];
      next.splice(actualIndex, 1);
      return next;
    });
  }

  function handleRemoveSelectedBox() {
    if (!selectedBoxId) return;
    const removedIndex = boxes.findIndex((b) => b.id === selectedBoxId);
    if (removedIndex === -1) return;

    setBoxes((prev) => prev.filter((b) => b.id !== selectedBoxId));
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
    setSortResult(null);
    setFillMessage("");
    setFocusedPlantName("");

    if (plan.metadata?.sortOptions) {
      setSortOptions((prev) => ({
        ...prev,
        ...plan.metadata.sortOptions,
      }));
    }
  }

  return (
    <div className="canvas-page">
      <header className="page-header">
        <div>
          <p className="page-kicker">Garden canvas</p>
          <h1 className="page-title">Place beds, crops, and companion groups.</h1>
          <p className="page-subtitle">
            Drag plants into beds, lock important placements, then use autosort to explore cleaner arrangements.
          </p>
        </div>
        <div className="selected-count">
          {plantInstances.length} plant{plantInstances.length === 1 ? "" : "s"} placed
        </div>
      </header>

      <div className="planner-layout">
        <div className="garden-panel">
          <GardenGrid
            boxes={boxes}
            setBoxes={setBoxes}
            selectedBoxId={selectedBoxId}
            setSelectedBoxId={setSelectedBoxId}
            sortResult={sortResult}
            plantInstances={plantInstances}
            setPlantInstances={setPlantInstances}
            plantsData={plantsData}
            focusedPlantName={focusedPlantName}
          />

          {notPlacedSummary.length > 0 && (
            <div className="alert alert-danger mt-3">
              <h5 className="alert-heading mb-2">
                Some plants could not be placed
              </h5>

              <p className="mb-2">
                The quick solver removed these plants because it could not fit them
                with the current options.
              </p>

              <div className="mb-3">
                <strong>Removed:</strong>{" "}
                {notPlacedSummary.map((item) => `${item.name} x ${item.count}`).join(", ")}
              </div>

              <button
                type="button"
                className="btn btn-danger"
                onClick={handleQuickMinSpaceResort}
                disabled={isSorting}
              >
                Add all missing plants back and rerun quick solver with relaxed spacing
              </button>

              <small className="text-muted d-block mt-2">
                This uses the full plant list from before the failed sort, but relaxes
                spacing so Quick has a better chance of placing everything.
              </small>
            </div>
          )}
        </div>

        <aside className="planner-sidebar">
          <SavedPlansPanel
            planType="garden"
            boxes={boxes}
            plantInstances={plantInstances}
            metadata={{ sortOptions }}
            initialPlanId={initialPlanId}
            onLoadPlan={handleLoadSavedPlan}
          />

          <SortingPanel
            sortOptions={sortOptions}
            setSortOptions={setSortOptions}
            onSort={handleSort}
            onForceStop={handleForceStop}
            isSorting={isSorting}
            progressPercent={progressPercent}
            progressLabel={progressLabel}
            estimatedTimeText={estimatedTimeText}
          />

          <BoxesPanel
            boxes={boxes}
            setBoxes={setBoxes}
            selectedBoxId={selectedBoxId}
            setSelectedBoxId={setSelectedBoxId}
            onRemoveSelected={handleRemoveSelectedBox}
            onClearSelected={handleClearSelectedBox}
          />

          <CRpanel
            plantInstances={plantInstances}
            plantsData={plantsData}
            sortResult={sortResult}
            onAddPlant={handleAddPlant}
            onCompanionFill={handleCompanionFill}
            getCompanionFitCount={countCompanionFitForCurrentGrid}
            isSorting={isSorting}
          />

          <div className="card p-3 my-3 selected-plants-card">
            <button
              type="button"
              className="btn btn-link panel-toggle text-decoration-none p-0 d-flex justify-content-between align-items-center w-100"
              onClick={() => setSelectedPlantsOpen((prev) => !prev)}
            >
              <h5 className="mb-0">Selected plants</h5>
              <span>{selectedPlantsOpen ? "Hide" : "Show"}</span>
            </button>

            {selectedPlantsOpen && (
              <>
                <button
                  type="button"
                  className="btn btn-outline-success w-100 my-2"
                  onClick={handleEqualFillSelectedTypes}
                  disabled={isSorting || fillablePlantSummary.length === 0}
                >
                  Fill equally with current plant types
                </button>
                <small className="text-muted d-block mb-2">
                  Adds more unlocked plant types already on the canvas, aiming for equal space per type. It tries companion overlap unless No companion overlap is enabled. Locked plants stay where they are and are not counted in the equal-space share.
                </small>
                {focusedPlantName && (
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary w-100 mb-2"
                    onClick={() => setFocusedPlantName("")}
                  >
                    Clear highlight
                  </button>
                )}
                {fillMessage && (
                  <div className="alert alert-info py-2 small mb-3">
                    {fillMessage}
                  </div>
                )}
                {plantSummary.length === 0 ? (
                  <small className="text-muted">No plants selected yet.</small>
                ) : (
                  <div className="d-grid gap-2">
                    {plantSummary.map((item) => {
                      const plant = plantsData.find((p) => p.name === item.name);
                      const colour = getPlantTypeColour(item.name);
                      const isFocused =
                        normalisePlantTypeName(focusedPlantName) === normalisePlantTypeName(item.name);

                      return (
                        <div
                          key={item.name}
                          className={`panel-section selected-plant-row p-2 d-flex justify-content-between align-items-center gap-2 ${isFocused ? "selected-plant-row-active" : ""}`}
                          role="button"
                          tabIndex={0}
                          onClick={() => toggleFocusedPlantName(item.name)}
                          onKeyDown={(event) => handlePlantSummaryKeyDown(event, item.name)}
                        >
                          <div className="selected-plant-main">
                            <span
                              className="plant-type-swatch"
                              style={{
                                background: colour.background,
                                borderColor: colour.border,
                              }}
                              title={`${colour.label} tile colour`}
                            />
                            <div>
                              <strong>{item.name}</strong>
                              <div className="small text-muted">On canvas: {item.count}</div>
                              <div className="small text-muted">Colour: {colour.label}</div>
                            </div>
                          </div>

                          <div className="d-flex align-items-center gap-2">
                            <button
                              type="button"
                              className="btn btn-sm btn-outline-secondary"
                              onClick={(event) => {
                                event.stopPropagation();
                                plant && handleRemovePlant(plant);
                              }}
                              disabled={!plant}
                            >
                              -
                            </button>

                            <span style={{ minWidth: "24px", textAlign: "center" }}>
                              {item.count}
                            </span>

                            <button
                              type="button"
                              className="btn btn-sm btn-outline-secondary"
                              onClick={(event) => {
                                event.stopPropagation();
                                plant && handleAddPlant(plant);
                              }}
                              disabled={!plant}
                            >
                              +
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </div>
          <PlantsPanel
            plantInstances={plantInstances}
            setPlantInstances={setPlantInstances}
            onPlantsLoaded={setPlantsData}
            onAddPlant={handleAddPlant}
            onRemovePlant={handleRemovePlant}
          />
        </aside>
      </div>
    </div>
  );
}

export default FreeMoveCanvas;
