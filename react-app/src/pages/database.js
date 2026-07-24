/**
 * @todo
 * this will be a page that will display a list of plants
 */
import { useQuery } from '@tanstack/react-query';
import { Col, Container, Row, Form, InputGroup  } from "react-bootstrap";
import Plant from "../components/Plant";
import Error from "../components/Error";
import Loading from "../components/Loading";
import { API } from "../constants";
import { useMemo, useState } from "react";
import { CATEGORY_OPTIONS, ROLE_FILTER_OPTIONS, labelForRole, rolesForPlant } from "../components/plantLabels";

function asPlantList(data) {
    if (Array.isArray(data)) return data;
    return data?.results ?? [];
}

function Database() {
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState("");
    const [roleFilter, setRoleFilter] = useState("");

	const { isPending, data, error } = useQuery({
		queryKey: ['plantData'],
		queryFn: async () => {
			const response = await fetch(`${API}plant/`)
			return await response.json();
		},
	})

    const filtered = useMemo(() => {
        const plants = asPlantList(data);

        const q = String(search || "").trim().toLowerCase();

        return plants.filter((p) => {
            const name = String(p?.name ?? "").toLowerCase();
            const plantCategory = String(p?.plant_category ?? "").toLowerCase();
            const rawRoles = rolesForPlant(p);
            const roleLabels = rawRoles.map((role) => labelForRole(role).toLowerCase());
            const matchesCategory = !category || plantCategory === category;
            const matchesRole = !roleFilter || rawRoles.includes(roleFilter);
            const matchesSearch =
                !q ||
                name.indexOf(q) !== -1 ||
                plantCategory.indexOf(q) !== -1 ||
                rawRoles.some((role) => String(role).toLowerCase().indexOf(q) !== -1) ||
                roleLabels.some((role) => role.indexOf(q) !== -1);

            return matchesCategory && matchesRole && matchesSearch;
        });
        }, [data, search, category, roleFilter]);

	if (isPending) return <Loading message="Loading..." />


	if (error) return <Error message="Could not load Plant" />

	return (
		<Container fluid className="px-0">
            <header className="page-header">
                <div>
                    <p className="page-kicker">Plant database</p>
                    <h1 className="page-title">Find the right plants for the plan.</h1>
                    <p className="page-subtitle">
                        Search by name, category, or growing role, then open a plant for spacing and companion details.
                    </p>
                </div>
            </header>

            <div className="toolbar-panel">
            <Row className="g-3 align-items-center">
                <Col xs={12} lg={4}>
                <InputGroup>
                    <Form.Control
                    type="text"
                    placeholder="Search plants, roles, or labels..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    />
                </InputGroup>
                </Col>

                <Col xs={12} sm={6} lg={3} className="mt-2 mt-lg-0">
                    <Form.Select
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        aria-label="Filter by plant type"
                    >
                        {CATEGORY_OPTIONS.map((option) => (
                            <option key={option.value || "all"} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </Form.Select>
                </Col>

                <Col xs={12} sm={6} lg={3} className="mt-2 mt-lg-0">
                    <Form.Select
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                        aria-label="Filter by plant use"
                    >
                        {ROLE_FILTER_OPTIONS.map((option) => (
                            <option key={option.value || "all-uses"} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </Form.Select>
                </Col>

                <Col xs={12} lg={2} className="d-flex align-items-center mt-2 mt-lg-0">
                <small className="selected-count">
                    Showing {filtered.length} of {asPlantList(data).length}
                </small>
                </Col>
            </Row>
            </div>

            <Row className="g-3">
            {filtered.map((b) => (
                <Col key={b.id} xs={12} md={4}>
                <Plant data={b} />
                </Col>
            ))}
            </Row>

            {filtered.length === 0 && (
                <div className="empty-state">
                    No plants match the current filters.
                </div>
            )}
		</Container>
	);
}

export default Database;
