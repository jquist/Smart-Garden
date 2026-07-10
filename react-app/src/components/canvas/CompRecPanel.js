import React, { useMemo, useState } from "react";
import { API } from "../../constants";

function asList(data) {
  if (Array.isArray(data)) return data;
  return data?.results ?? [];
}

function CRPanel({
  plantInstances,
  plantsData,
  sortResult,
  onAddPlant,
  onCompanionFill,
  getCompanionFitCount,
  isSorting = false,
}) {
  const [open, setOpen] = useState(true);
  const [recommendations, setRecommendations] = useState({
    primary: [],
    secondary: [],
    avoided: [],
  });
  const [fitCountsByName, setFitCountsByName] = useState({});
  const [selectedNames, setSelectedNames] = useState(() => new Set());
  const [placementMode, setPlacementMode] = useState("best");
  const [loading, setLoading] = useState(false);
  const [lastRefreshText, setLastRefreshText] = useState("");

  const gardenPlants = useMemo(() => {
    const map = new Map();

    for (const plant of plantInstances) {
      if (!plant.plantId) continue;
      if (!map.has(plant.plantId)) {
        map.set(plant.plantId, {
          id: plant.plantId,
          name: plant.name,
        });
      }
    }

    return Array.from(map.values());
  }, [plantInstances]);

  const recommendationNames = useMemo(() => {
    return [
      ...recommendations.primary.map((item) => item.name),
      ...recommendations.secondary.map((item) => item.name),
    ];
  }, [recommendations]);

  function calculateFitCounts(names) {
    const counts = {};

    for (const name of names) {
      counts[name] = getCompanionFitCount ? getCompanionFitCount(name) : 0;
    }

    setFitCountsByName(counts);
    return counts;
  }

  async function refreshRecommendations() {
    if (gardenPlants.length === 0) {
      setRecommendations({ primary: [], secondary: [], avoided: [] });
      setFitCountsByName({});
      setSelectedNames(new Set());
      setLastRefreshText("Add a plant to the canvas, then refresh recommendations.");
      return;
    }

    setLoading(true);

    try {
      const primaryScores = new Map();
      const secondaryScores = new Map();
      const avoidNames = new Set();
      const existingNames = new Set(
        gardenPlants.map((p) => String(p.name).toLowerCase())
      );

      for (const plant of gardenPlants) {
        const [helpByRes, helpRes, avoidRes] = await Promise.all([
          fetch(`${API}help_by/?plant=${plant.id}`),
          fetch(`${API}help/?plant=${plant.id}`),
          fetch(`${API}avoid/?plant=${plant.id}`),
        ]);

        if (!helpByRes.ok || !helpRes.ok || !avoidRes.ok) {
          throw new Error("Could not refresh companion recommendations.");
        }

        const helpByData = asList(await helpByRes.json());
        const helpData = asList(await helpRes.json());
        const avoidData = asList(await avoidRes.json());

        // PRIMARY: plants that help the existing garden plant.
        for (const item of helpByData) {
          const name = item.other_plant_name;
          if (!name) continue;

          const key = name.toLowerCase();
          if (existingNames.has(key)) continue;

          primaryScores.set(name, (primaryScores.get(name) || 0) + 1);
        }

        // SECONDARY: plants that the existing garden plant would help.
        for (const item of helpData) {
          const name = item.other_plant_name;
          if (!name) continue;

          const key = name.toLowerCase();
          if (existingNames.has(key)) continue;

          secondaryScores.set(name, (secondaryScores.get(name) || 0) + 1);
        }

        for (const item of avoidData) {
          if (item.other_plant_name) {
            avoidNames.add(item.other_plant_name.toLowerCase());
          }
        }
      }

      function toSortedList(scoreMap) {
        return Array.from(scoreMap.entries())
          .filter(([name]) => !avoidNames.has(name.toLowerCase()))
          .map(([name, score]) => ({ name, score }))
          .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
      }

      const primary = toSortedList(primaryScores);
      const primaryNames = new Set(primary.map((p) => p.name.toLowerCase()));
      const secondary = toSortedList(secondaryScores).filter(
        (p) => !primaryNames.has(p.name.toLowerCase())
      );

      const nextRecommendations = {
        primary,
        secondary,
        avoided: Array.from(avoidNames).sort(),
      };

      const names = [
        ...nextRecommendations.primary.map((item) => item.name),
        ...nextRecommendations.secondary.map((item) => item.name),
      ];

      setRecommendations(nextRecommendations);
      calculateFitCounts(names);
      setSelectedNames((prev) => {
        const validNames = new Set(names);
        return new Set(Array.from(prev).filter((name) => validNames.has(name)));
      });
      setLastRefreshText(`Last refreshed for ${gardenPlants.length} plant type${gardenPlants.length === 1 ? "" : "s"} on the canvas.`);
    } catch (error) {
      console.error(error);
      setRecommendations({ primary: [], secondary: [], avoided: [] });
      setFitCountsByName({});
      setLastRefreshText("Could not refresh recommendations.");
    } finally {
      setLoading(false);
    }
  }

  function refreshFitCountsOnly() {
    if (recommendationNames.length === 0) {
      setFitCountsByName({});
      setLastRefreshText("Refresh recommendations first.");
      return;
    }

    calculateFitCounts(recommendationNames);
    setLastRefreshText("Fit counts refreshed from the current canvas.");
  }

  function toggleName(name) {
    setSelectedNames((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  function addSelectedPlants() {
    for (const name of selectedNames) {
      const plant = plantsData.find(
        (p) => String(p.name).toLowerCase() === String(name).toLowerCase()
      );

      if (plant) {
        onAddPlant(plant, { preferCompanionOverlap: true });
      }
    }

    setSelectedNames(new Set());
    setLastRefreshText("Plants added. Press Refresh fit counts to update the numbers.");
  }

  function companionFillSelected() {
    onCompanionFill?.(selectedNames, placementMode);
    setSelectedNames(new Set());
    setLastRefreshText("Companion fill ran. Press Refresh fit counts to update the numbers.");
  }

  function RecommendationList({ items }) {
    if (items.length === 0) {
      return <small className="text-muted">No recommendations found.</small>;
    }

    return (
      <div>
        {items.map((item) => {
          const canFit = fitCountsByName[item.name];
          const hasFitCount = typeof canFit === "number";
          const disabled = hasFitCount && canFit <= 0;

          return (
            <label
              key={item.name}
              className={`border rounded p-2 mb-2 d-flex justify-content-between align-items-center ${
                disabled ? "text-muted" : ""
              }`}
              style={{ cursor: disabled || isSorting ? "not-allowed" : "pointer" }}
            >
              <div>
                <strong>{item.name}</strong>
                <div className="small text-muted">
                  Helps {item.score} selected plant{item.score === 1 ? "" : "s"}
                </div>
                {!hasFitCount ? (
                  <div className="small text-muted">Press refresh to calculate fit.</div>
                ) : (
                  <div className={canFit > 0 ? "small text-success" : "small text-danger"}>
                    {canFit > 0 ? `Can fit: ${canFit}` : "No valid companion space right now"}
                  </div>
                )}
              </div>

              <input
                type="checkbox"
                checked={selectedNames.has(item.name)}
                disabled={disabled || isSorting}
                onChange={() => toggleName(item.name)}
              />
            </label>
          );
        })}
      </div>
    );
  }

  return (
    <div className="card p-3 mb-3">
      <div className="d-flex justify-content-between align-items-center gap-2">
        <button
          type="button"
          className="btn btn-link text-decoration-none p-0 d-flex justify-content-between align-items-center flex-grow-1"
          onClick={() => setOpen((prev) => !prev)}
        >
          <h5 className="mb-0">Companion recommendations</h5>
          <span className="ms-2">{open ? "▲" : "▼"}</span>
        </button>

        <button
          type="button"
          className="btn btn-sm btn-outline-primary"
          disabled={loading || isSorting}
          onClick={refreshRecommendations}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {open && (
        <>
          <p className="small text-muted mt-3 mb-2">
            Recommendations and fit counts only update when you press Refresh, so dragging plants will not spam backend requests.
          </p>

          {lastRefreshText && (
            <div className="alert alert-info py-2 small mb-3">
              {lastRefreshText}
            </div>
          )}

          {gardenPlants.length === 0 ? (
            <small className="text-muted d-block mb-3">
              Add at least one plant to the canvas, then press Refresh.
            </small>
          ) : loading ? (
            <p>Finding companions...</p>
          ) : (
            <>
              <div className="mb-3">
                <label className="form-label small mb-1">Placement mode</label>
                <div className="d-flex gap-2">
                  <select
                    className="form-select form-select-sm"
                    value={placementMode}
                    disabled={isSorting}
                    onChange={(e) => setPlacementMode(e.target.value)}
                  >
                    <option value="best">Best single fit</option>
                    <option value="smart">Smart gap fill</option>
                    <option value="maximise">Maximise companion fill</option>
                  </select>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    disabled={isSorting || recommendationNames.length === 0}
                    onClick={refreshFitCountsOnly}
                  >
                    Refresh fit counts
                  </button>
                </div>
                <small className="text-muted d-block mt-1">
                  Companion fill adds plants without moving anything already on the canvas.
                </small>
              </div>

              <h6>Best recommendations</h6>
              <p className="small text-muted">
                These plants may help the plants already in your garden.
              </p>
              <RecommendationList items={recommendations.primary} />

              <hr />

              <h6>Optional compatible plants</h6>
              <p className="small text-muted">
                These plants may benefit from your garden, but are less directly useful to the plants you already chose.
              </p>
              <RecommendationList items={recommendations.secondary} />

              <button
                className="btn btn-outline-success w-100 mt-2"
                disabled={selectedNames.size === 0 || isSorting}
                onClick={addSelectedPlants}
              >
                Add selected recommendations
              </button>
              <button
                className="btn btn-success w-100 mt-2"
                disabled={selectedNames.size === 0 || isSorting}
                onClick={companionFillSelected}
              >
                Fill gaps with selected companions
              </button>
            </>
          )}
        </>
      )}
    </div>
  );
}

export default CRPanel;
