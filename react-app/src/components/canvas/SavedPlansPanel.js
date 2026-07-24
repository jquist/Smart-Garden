import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch, useAuth } from "../../auth/AuthContext";

function formatPlanDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleString([], {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function SavedPlansPanel({
  planType,
  boxes,
  plantInstances,
  metadata = {},
  initialPlanId = "",
  onLoadPlan,
}) {
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loadedPlan, setLoadedPlan] = useState(null);
  const [loadedInitialPlanId, setLoadedInitialPlanId] = useState("");
  const [selectedPlanId, setSelectedPlanId] = useState("");
  const [saveName, setSaveName] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const onLoadPlanRef = useRef(onLoadPlan);

  useEffect(() => {
    onLoadPlanRef.current = onLoadPlan;
  }, [onLoadPlan]);

  const selectedPlan = useMemo(
    () =>
      plans.find((plan) => String(plan.id) === String(selectedPlanId)) ||
      (loadedPlan && String(loadedPlan.id) === String(selectedPlanId) ? loadedPlan : null),
    [loadedPlan, plans, selectedPlanId]
  );

  const loadPlans = useCallback(async () => {
    if (!user) return;

    setLoading(true);
    setMessage("");

    try {
      const data = await apiFetch(`garden-plans/?plan_type=${encodeURIComponent(planType)}`);
      setPlans(Array.isArray(data) ? data : data?.results || []);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }, [planType, user]);

  useEffect(() => {
    if (!user) {
      setPlans([]);
      setLoadedPlan(null);
      setLoadedInitialPlanId("");
      setSelectedPlanId("");
      setSaveName("");
      return;
    }

    loadPlans();
  }, [loadPlans, user]);

  useEffect(() => {
    if (selectedPlan) {
      setSaveName(selectedPlan.name);
    }
  }, [selectedPlan]);

  const applyLoadedPlan = useCallback((plan, nextMessage = "Planner loaded.") => {
    setLoadedPlan(plan);
    setSelectedPlanId(String(plan.id));
    setSaveName(plan.name || "");
    onLoadPlanRef.current?.(plan);
    setMessage(nextMessage);
  }, []);

  const loadPlanById = useCallback(async (planId) => {
    if (!user || !planId) return;

    setLoading(true);
    setMessage("");

    try {
      const plan = await apiFetch(`garden-plans/${encodeURIComponent(planId)}/`);
      if (plan.plan_type !== planType) {
        throw new Error("This saved planner belongs to a different tool.");
      }

      applyLoadedPlan(plan, "Planner loaded from Projects.");
      setPlans((prev) => {
        const withoutLoaded = prev.filter((item) => String(item.id) !== String(plan.id));
        return [plan, ...withoutLoaded];
      });
      setLoadedInitialPlanId(String(planId));
    } catch (error) {
      setMessage(error.message);
      setLoadedInitialPlanId(String(planId));
    } finally {
      setLoading(false);
    }
  }, [applyLoadedPlan, planType, user]);

  useEffect(() => {
    const planId = String(initialPlanId || "").trim();
    if (!user || !planId || loadedInitialPlanId === planId) return;
    loadPlanById(planId);
  }, [initialPlanId, loadPlanById, loadedInitialPlanId, user]);

  async function savePlan({ updateExisting = false } = {}) {
    const name = saveName.trim();
    if (!name) {
      setMessage("Give the planner a name first.");
      return;
    }

    const payload = {
      name,
      plan_type: planType,
      boxes,
      plant_instances: plantInstances,
      metadata,
    };

    const shouldUpdate = updateExisting && selectedPlan;

    setLoading(true);
    setMessage("");

    try {
      const saved = await apiFetch(
        shouldUpdate ? `garden-plans/${selectedPlan.id}/` : "garden-plans/",
        {
          method: shouldUpdate ? "PUT" : "POST",
          body: JSON.stringify(payload),
        }
      );
      setMessage(shouldUpdate ? "Planner updated." : "Planner saved.");
      setSelectedPlanId(String(saved.id));
      setLoadedPlan(saved);
      await loadPlans();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function deletePlan() {
    if (!selectedPlan) return;

    setLoading(true);
    setMessage("");

    try {
      await apiFetch(`garden-plans/${selectedPlan.id}/`, {
        method: "DELETE",
      });
      setLoadedPlan(null);
      setSelectedPlanId("");
      setSaveName("");
      setMessage("Planner deleted.");
      await loadPlans();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  function loadSelectedPlan() {
    if (!selectedPlan) return;
    applyLoadedPlan(selectedPlan);
  }

  return (
    <div className="card p-3 mb-3 saved-plans-card">
      <h5 className="mb-2">Saved planners</h5>

      {!user ? (
        <small className="text-muted">
          Log in or sign up from the top bar to save and load your garden planners.
        </small>
      ) : (
        <>
          <label className="saved-plan-field">
            <span>Name</span>
            <input
              type="text"
              className="form-control"
              value={saveName}
              placeholder="My spring garden"
              onChange={(event) => setSaveName(event.target.value)}
            />
          </label>

          <label className="saved-plan-field">
            <span>Saved list</span>
            <select
              className="form-select"
              value={selectedPlanId}
              onChange={(event) => setSelectedPlanId(event.target.value)}
            >
              <option value="">New planner</option>
              {plans.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.name} {plan.updated_at ? `- ${formatPlanDate(plan.updated_at)}` : ""}
                </option>
              ))}
            </select>
          </label>

          <div className="saved-plan-actions">
            <button
              type="button"
              className="btn btn-success"
              onClick={() => savePlan({ updateExisting: false })}
              disabled={loading}
            >
              Save new
            </button>
            <button
              type="button"
              className="btn btn-outline-success"
              onClick={() => savePlan({ updateExisting: true })}
              disabled={loading || !selectedPlan}
            >
              Update
            </button>
            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={loadSelectedPlan}
              disabled={!selectedPlan}
            >
              Load
            </button>
            <button
              type="button"
              className="btn btn-outline-danger"
              onClick={deletePlan}
              disabled={loading || !selectedPlan}
            >
              Delete
            </button>
          </div>

          {message && <div className="alert alert-info py-2 small mb-0">{message}</div>}
          {loading && <small className="text-muted">Working...</small>}
        </>
      )}
    </div>
  );
}

export default SavedPlansPanel;
