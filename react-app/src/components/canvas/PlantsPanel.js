import React, { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { API } from "../../constants";

function PlantsPanel({
  plantInstances,
  onPlantsLoaded,
  onAddPlant,
  onRemovePlant,
}) {
  const [open, setOpen] = useState(true);
  const [search, setSearch] = useState("");

  const { data = [], isPending, error } = useQuery({
    queryKey: ["canvasPlants"],
    queryFn: async () => {
      const response = await fetch(`${API}plant`);
      if (!response.ok) {
        throw new Error("Failed to load plants");
      }
      return response.json();
    },
  });

  useEffect(() => {
    onPlantsLoaded?.(data);
  }, [data, onPlantsLoaded]);

  function handleDragStart(e, plant) {
    e.dataTransfer.setData(
      "application/json",
      JSON.stringify({
        source: "plants-panel",
        plantId: plant.id,
        name: plant.name,
      })
    );
    e.dataTransfer.effectAllowed = "copy";
  }

  const countsByPlantId = useMemo(() => {
    const counts = {};
    for (const instance of plantInstances) {
      counts[instance.plantId] = (counts[instance.plantId] || 0) + 1;
    }
    return counts;
  }, [plantInstances]);

  const filteredPlants = useMemo(() => {
    const q = search.trim().toLowerCase();

    return data
      .filter((plant) =>
        !q || String(plant.name || "").toLowerCase().includes(q)
      )
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [data, search]);

  return (
    <div className="card p-3 mb-3">
      <button
        type="button"
        className="btn btn-link text-decoration-none p-0 d-flex justify-content-between align-items-center w-100"
        onClick={() => setOpen((prev) => !prev)}
      >
        <h5 className="mb-0">Plants</h5>
        <span>{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <>
          <input
            type="text"
            className="form-control my-3"
            placeholder="Search plants..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <div className="small text-muted mb-3">
            Drag into a box or use + to add. - removes from the same shared plant list.
          </div>

          {isPending && <p>Loading plants...</p>}
          {error && <p>Could not load plants.</p>}

          <div style={{ maxHeight: "400px", overflowY: "auto" }}>
            {filteredPlants.map((plant) => {
              const count = countsByPlantId[plant.id] || 0;

              return (
                <div
                  key={plant.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, plant)}
                  className={`border rounded p-2 mb-2 ${
                    count > 0 ? "border-primary bg-light" : ""
                  }`}
                  style={{
                    cursor: "grab",
                    userSelect: "none",
                  }}
                >
                  <div className="d-flex justify-content-between align-items-center gap-2">
                    <div>
                      <strong>{plant.name}</strong>
                      <div className="small text-muted">
                        {plant.spacing_between_rows || 0}cm spacing
                      </div>
                    </div>

                    <div className="d-flex align-items-center gap-2">
                      <button
                        className="btn btn-sm btn-outline-secondary"
                        onClick={() => onRemovePlant(plant)}
                      >
                        -
                      </button>

                      <span style={{ minWidth: "24px", textAlign: "center" }}>
                        {count}
                      </span>

                      <button
                        className="btn btn-sm btn-outline-secondary"
                        onClick={() => onAddPlant(plant)}
                      >
                        +
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

export default PlantsPanel;