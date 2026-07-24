import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import Error from "../components/Error";
import Loading from "../components/Loading";
import { apiFetch, useAuth } from "../auth/AuthContext";
import {
  getBoardBounds,
  getPlantTypeColour,
  withAbsolutePlantPosition,
} from "../components/canvas/canvasUtils";

function formatDate(value) {
  if (!value) return "Not saved yet";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not saved yet";

  return date.toLocaleString([], {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function planTypeLabel(planType) {
  return planType === "weed" ? "Weed control" : "Garden planner";
}

function canvasPathForPlan(plan) {
  return plan.plan_type === "weed"
    ? `/weed-control?plan=${plan.id}`
    : `/canvas?plan=${plan.id}`;
}

function plantKindLabel(kind) {
  if (kind === "weed") return "Weed";
  if (kind === "weed_control") return "Suppressor";
  return "Plant";
}

function getPlantSummary(plan) {
  const counts = new Map();
  const instances = Array.isArray(plan?.plant_instances) ? plan.plant_instances : [];

  for (const instance of instances) {
    const name = String(instance?.name || "Unnamed plant").trim();
    const kind = plantKindLabel(instance?.kind);
    const key = `${kind}:${name.toLowerCase()}`;
    const current = counts.get(key) || { name, kind, count: 0 };
    counts.set(key, { ...current, count: current.count + 1 });
  }

  return Array.from(counts.values()).sort(
    (a, b) => a.kind.localeCompare(b.kind) || a.name.localeCompare(b.name)
  );
}

function ProjectLayoutPreview({ plan }) {
  const boxes = Array.isArray(plan?.boxes) ? plan.boxes : [];
  const plants = Array.isArray(plan?.plant_instances) ? plan.plant_instances : [];
  const bounds = getBoardBounds(boxes);
  const shownPlants = plants.slice(0, 42);

  if (boxes.length === 0) {
    return (
      <div className="project-layout-preview project-layout-preview-empty">
        No layout saved yet
      </div>
    );
  }

  return (
    <div className="project-layout-preview" aria-label={`${plan.name} saved layout preview`}>
      {boxes.map((box) => (
        <span
          key={box.id}
          className="project-layout-box"
          style={{
            left: `${(box.x / bounds.cols) * 100}%`,
            top: `${(box.y / bounds.rows) * 100}%`,
            width: `${(box.w / bounds.cols) * 100}%`,
            height: `${(box.h / bounds.rows) * 100}%`,
          }}
        />
      ))}

      {shownPlants.map((plant, index) => {
        const positioned = withAbsolutePlantPosition(plant, boxes);
        const colour = getPlantTypeColour(plant.name);
        const isWeed = plant.kind === "weed";

        return (
          <span
            key={plant.id || `${plant.name}-${index}`}
            className="project-layout-plant"
            title={plant.name}
            style={{
              left: `${(positioned.col / bounds.cols) * 100}%`,
              top: `${(positioned.row / bounds.rows) * 100}%`,
              width: `${Math.max(4, (Number(positioned.width || 1) / bounds.cols) * 100)}%`,
              height: `${Math.max(4, (Number(positioned.height || 1) / bounds.rows) * 100)}%`,
              background: isWeed ? "rgba(143, 45, 45, 0.28)" : colour.background,
              borderColor: isWeed ? "rgba(143, 45, 45, 0.82)" : colour.border,
            }}
          />
        );
      })}

      {plants.length > shownPlants.length && (
        <span className="project-layout-more">+{plants.length - shownPlants.length}</span>
      )}
    </div>
  );
}

function ProjectPlantList({ summary }) {
  if (summary.length === 0) {
    return <small className="text-muted">No plants have been saved in this project yet.</small>;
  }

  return (
    <div className="project-plant-list">
      {summary.slice(0, 8).map((item) => {
        const colour = getPlantTypeColour(item.name);

        return (
          <div key={`${item.kind}-${item.name}`} className="project-plant-row">
            <span
              className="plant-type-swatch"
              style={{ background: colour.background, borderColor: colour.border }}
              title={`${colour.label} tile colour`}
            />
            <span>
              <strong>{item.name}</strong>
              <small>{item.kind}</small>
            </span>
            <b>x {item.count}</b>
          </div>
        );
      })}

      {summary.length > 8 && (
        <small className="text-muted">+ {summary.length - 8} more plant type{summary.length - 8 === 1 ? "" : "s"}</small>
      )}
    </div>
  );
}

function Projects() {
  const { user, loading: authLoading } = useAuth();
  const [deletingId, setDeletingId] = useState("");

  const {
    data,
    isPending,
    error,
    refetch,
  } = useQuery({
    queryKey: ["gardenProjects", user?.id],
    enabled: Boolean(user),
    queryFn: async () => {
      const plans = await apiFetch("garden-plans/");
      return Array.isArray(plans) ? plans : plans?.results || [];
    },
  });

  const plans = useMemo(() => (Array.isArray(data) ? data : []), [data]);

  async function deleteProject(plan) {
    if (!plan) return;

    setDeletingId(String(plan.id));
    try {
      await apiFetch(`garden-plans/${plan.id}/`, { method: "DELETE" });
      await refetch();
    } catch (deleteError) {
      alert(deleteError.message || "Could not delete that project.");
    } finally {
      setDeletingId("");
    }
  }

  if (authLoading) return <Loading message="Checking account..." />;

  if (!user) {
    return (
      <div className="projects-page">
        <header className="page-header">
          <div>
            <p className="page-kicker">Projects</p>
            <h1 className="page-title">Saved gardens live here.</h1>
            <p className="page-subtitle">
              Log in or sign up from the top bar to save garden layouts and open them again later.
            </p>
          </div>
        </header>

        <div className="empty-state account-empty">
          Your projects will appear here once you are logged in.
        </div>
      </div>
    );
  }

  if (isPending) return <Loading message="Loading saved gardens..." />;
  if (error) return <Error message="Could not load saved gardens" />;

  return (
    <div className="projects-page">
      <header className="page-header">
        <div>
          <p className="page-kicker">Projects</p>
          <h1 className="page-title">Your saved garden projects.</h1>
          <p className="page-subtitle">
            Open a saved layout in the canvas, or send its plant list straight to the growing calendar.
          </p>
        </div>
        <div className="selected-count">
          {plans.length} project{plans.length === 1 ? "" : "s"}
        </div>
      </header>

      <div className="project-toolbar">
        <Link to="/canvas" className="btn btn-success">
          New garden
        </Link>
        <Link to="/weed-control" className="btn btn-outline-success">
          New weed-control plan
        </Link>
        <Link to="/profile" className="btn btn-outline-primary">
          Profile
        </Link>
      </div>

      {plans.length === 0 ? (
        <div className="empty-state">
          No saved garden projects yet. Start a garden or weed-control plan, then save it.
        </div>
      ) : (
        <div className="projects-grid">
          {plans.map((plan) => {
            const summary = getPlantSummary(plan);
            const boxes = Array.isArray(plan.boxes) ? plan.boxes : [];
            const plants = Array.isArray(plan.plant_instances) ? plan.plant_instances : [];

            return (
              <article key={plan.id} className="project-card">
                <div className="project-card-header">
                  <div>
                    <span className="project-type-pill">{planTypeLabel(plan.plan_type)}</span>
                    <h2>{plan.name}</h2>
                    <p>Last saved {formatDate(plan.updated_at)}</p>
                  </div>
                </div>

                <ProjectLayoutPreview plan={plan} />

                <div className="project-stats">
                  <span>{boxes.length} bed{boxes.length === 1 ? "" : "s"}</span>
                  <span>{plants.length} item{plants.length === 1 ? "" : "s"}</span>
                  <span>{summary.length} plant type{summary.length === 1 ? "" : "s"}</span>
                </div>

                <ProjectPlantList summary={summary} />

                <div className="project-actions">
                  <Link to={canvasPathForPlan(plan)} className="btn btn-success">
                    Open canvas
                  </Link>
                  <Link to={`/scheduler?plan=${plan.id}`} className="btn btn-outline-primary">
                    Scheduler
                  </Link>
                  <button
                    type="button"
                    className="btn btn-outline-danger"
                    onClick={() => deleteProject(plan)}
                    disabled={deletingId === String(plan.id)}
                  >
                    {deletingId === String(plan.id) ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Projects;
