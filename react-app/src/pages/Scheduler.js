/**
 * Scheduler page
 * - Left: chart (range-bar timeline)
 * - Right: search + plant cards
 */
import { useQuery } from "@tanstack/react-query";
import { Col, Container, Row, Form, InputGroup } from "react-bootstrap";
import { useCallback, useMemo, useState } from "react";

import Plant from "../components/Plant";
import Error from "../components/Error";
import Loading from "../components/Loading";
import { API } from "../constants";

import { AgCharts } from "ag-charts-react";
import {
  AnimationModule,
  CategoryAxisModule,
  ContextMenuModule,
  CrosshairModule,
  LegendModule,
  ModuleRegistry,
  NumberAxisModule,
  RangeBarSeriesModule,
} from "ag-charts-enterprise";

/* ---------------- MODULE REGISTRATION ---------------- */
ModuleRegistry.registerModules([
  AnimationModule,
  CategoryAxisModule,
  NumberAxisModule,
  RangeBarSeriesModule,
  CrosshairModule,
  LegendModule,
  ContextMenuModule,
]);

/* ---------------- CONSTANTS ---------------- */
const MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const monthToNumber = (month) => {
  if (!month) return null;

  const clean = month.toLowerCase().trim();

  const map = {
    january: 1,
    february: 2,
    febuary: 2,
    march: 3,
    april: 4,
    apirl: 4,
    may: 5,
    june: 6,
    july: 7,
    august: 8,
    september: 9,
    septemeber: 9,
    septemer: 9,
    october: 10,
    november: 11,
    novmeber: 11,
    december: 12,
  };

  return map[clean] ?? null;
};

function Scheduler() {
  const PANEL_H = "calc(100vh - 110px)";

  const [search, setSearch] = useState("");

  const { isPending, data, error } = useQuery({
    queryKey: ["plantData"],
    queryFn: async () => {
      const response = await fetch(`${API}plant/`);
      return await response.json();
    },
  });

  const [selectedIds, setSelectedIds] = useState(() => new Set());

  const filtered = useMemo(() => {
    if (!Array.isArray(data)) return [];

    const q = String(search || "").trim().toLowerCase();
    if (!q) return data;

    return data.filter((p) => {
      const name = String(p?.name ?? "").toLowerCase();
      return name.indexOf(q) !== -1;
    });
  }, [data, search]);

  const selectedPlants = useMemo(() => {
    if (!Array.isArray(data)) return [];
    return data.filter((p) => selectedIds.has(p.id));
  }, [data, selectedIds]);

  const chartPlants = useMemo(() => {
    if (!Array.isArray(data)) return [];
    return selectedPlants.length === 0 ? data : selectedPlants;
  }, [data, selectedPlants]);

  const monthIdx0 = useCallback((name) => {
    const m = monthToNumber(name);
    return Number.isFinite(m) ? m - 1 : null;
  }, []);

  const rangeWithinYear0 = useCallback((startName, endName) => {
    const s = monthIdx0(startName);
    const e = monthIdx0(endName);
    if (s == null || e == null) return null;

    const low = Math.min(s, e);
    const highExclusive = Math.max(s, e) + 1;
    return { low, highExclusive };
  }, [monthIdx0]);

  const absoluteRows = useMemo(() => {
    return chartPlants
      .map((p) => {
        const ps = monthIdx0(p.plant_start);
        const pe = monthIdx0(p.plant_end);
        if (ps == null || pe == null) return null;

        const plantLow = Math.min(ps, pe);
        const plantHigh = Math.max(ps, pe) + 1;

        const t = Number(p.time_first_harvets);
        const firstHarvestAbs = Number.isFinite(t) ? plantLow + t : null;

        const harvestTemplate = rangeWithinYear0(p.harest_start, p.harest_end);
        const germTemplate = rangeWithinYear0(
          p.time_to_germinate_indoors_start,
          p.time_to_germinate_indoors_end
        );

        return {
          plant: p.name,
          plantLow,
          plantHigh,
          germLow: germTemplate?.low ?? null,
          germHigh: germTemplate?.highExclusive ?? null,
          harvestTplLow: harvestTemplate?.low ?? null,
          harvestTplHigh: harvestTemplate?.highExclusive ?? null,
          firstHarvestAbs,
        };
      })
      .filter(Boolean);
  }, [chartPlants, monthIdx0, rangeWithinYear0]);

  const yearsNeeded = useMemo(() => {
    let maxEnd = 0;

    for (const r of absoluteRows) {
      maxEnd = Math.max(
        maxEnd,
        r.germHigh ?? 0,
        r.plantHigh ?? 0,
        r.harvestTplHigh ?? 0,
        r.firstHarvestAbs != null ? r.firstHarvestAbs + 1 : 0
      );
    }

    return Math.max(1, Math.ceil(maxEnd / 12));
  }, [absoluteRows]);

  const sliceYear = (rows, yearIndex) => {
    const yearStart = yearIndex * 12;
    const yearEnd = yearStart + 12;

    const clipAbs = (low, high) => {
      if (low == null || high == null) return [null, null];
      const l = Math.max(low, yearStart);
      const h = Math.min(high, yearEnd);
      if (h <= l) return [null, null];
      return [l - yearStart, h - yearStart];
    };

    return rows.map((r) => {
      const [pL, pH] = clipAbs(r.plantLow, r.plantHigh);

      const germAbsLow = r.germLow != null ? r.germLow : null;
      const germAbsHigh = r.germHigh != null ? r.germHigh : null;
      const [gL, gH] = clipAbs(germAbsLow, germAbsHigh);

      let hL = null;
      let hH = null;

      if (
        r.firstHarvestAbs != null &&
        r.harvestTplLow != null &&
        r.harvestTplHigh != null
      ) {
        const firstHarvestYear = Math.floor(r.firstHarvestAbs / 12);

        if (yearIndex >= firstHarvestYear) {
          const harvestAbsLow = yearIndex * 12 + r.harvestTplLow;
          const harvestAbsHigh = yearIndex * 12 + r.harvestTplHigh;

          if (yearIndex === firstHarvestYear) {
            const minAllowed = r.firstHarvestAbs;
            const lowAdj = Math.max(harvestAbsLow, minAllowed);
            [hL, hH] = clipAbs(lowAdj, harvestAbsHigh);
          } else {
            [hL, hH] = clipAbs(harvestAbsLow, harvestAbsHigh);
          }
        }
      }

      return {
        plant: r.plant,
        plantLow: pL,
        plantHigh: pH,
        germLow: gL,
        germHigh: gH,
        harvestLow: hL,
        harvestHigh: hH,
      };
    });
  };

  const addPlant = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  };

  const removePlant = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  };

  const isSelected = (id) => selectedIds.has(id);

  if (isPending) return <Loading message="Loading..." />;
  if (error) return <Error message="Could not load plants" />;

  return (
    <Container fluid className="p-2">
      <Row className="g-4">
        <Col md={6}>
          <div style={{ height: PANEL_H, overflowY: "auto" }}>
            {Array.from({ length: yearsNeeded }).map((_, i) => {
              const yearData = sliceYear(absoluteRows, i);

              const options = {
                data: yearData,
                title: { text: `Year ${i + 1}` },
                legend: { enabled: true },

                series: [
                  {
                    type: "range-bar",
                    direction: "horizontal",
                    xKey: "plant",
                    yLowKey: "germLow",
                    yHighKey: "germHigh",
                    yName: "Indoor germination",
                    fill: "#7aa7ff",
                  },
                  {
                    type: "range-bar",
                    direction: "horizontal",
                    xKey: "plant",
                    yLowKey: "plantLow",
                    yHighKey: "plantHigh",
                    yName: "Planting",
                    fill: "#58c27d",
                  },
                  {
                    type: "range-bar",
                    direction: "horizontal",
                    xKey: "plant",
                    yLowKey: "harvestLow",
                    yHighKey: "harvestHigh",
                    yName: "Harvest",
                    fill: "#ff9b6a",
                  },
                ],

                axes: [
                  { type: "category", position: "left", title: { text: "Plants" } },
                  {
                    type: "number",
                    position: "bottom",
                    min: 0,
                    max: 12,
                    nice: false,
                    interval: { step: 1 },
                    label: {
                      formatter: ({ value }) =>
                        value >= 0 && value <= 11 ? MONTHS[value + 1] : "",
                    },
                  },
                ],
              };

              return (
                <div key={i} style={{ height: 320, marginBottom: 16 }}>
                  <AgCharts options={options} />
                </div>
              );
            })}
          </div>

          <div className="mt-2 text-muted">
            Selected: {selectedPlants.length}
          </div>
        </Col>

        <Col md={6}>
          <Row className="mb-3">
            <Col xs={12}>
              <InputGroup>
                <InputGroup.Text>🔎</InputGroup.Text>
                <Form.Control
                  type="text"
                  placeholder="Search plants (e.g. tomato, basil)..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </InputGroup>
            </Col>
          </Row>

          <div style={{ flex: 1, overflowY: "auto", paddingRight: 6 }}>
            <Row className="g-3">
              {filtered.map((p) => (
                <Col key={p.id} xs={12} md={6}>
                  <div className="d-flex align-items-center gap-2">
                    {isSelected(p.id) ? (
                      <button
                        className="btn btn-outline-danger btn-sm"
                        onClick={() => removePlant(p.id)}
                        aria-label={`Remove ${p.name} from graph`}
                      >
                        −
                      </button>
                    ) : (
                      <button
                        className="btn btn-outline-success btn-sm"
                        onClick={() => addPlant(p.id)}
                        aria-label={`Add ${p.name} to graph`}
                      >
                        +
                      </button>
                    )}

                    <div className="flex-grow-1">
                      <Plant data={p} disableLink />
                    </div>
                  </div>
                </Col>
              ))}
            </Row>
          </div>
        </Col>
      </Row>
    </Container>
  );
}

export default Scheduler;
