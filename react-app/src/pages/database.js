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
import { CATEGORY_OPTIONS, labelForRole, rolesForPlant } from "../components/plantLabels";

function Database() {
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState("");

	const { isPending, data, error } = useQuery({
		queryKey: ['plantData'],
		queryFn: async () => {
			const response = await fetch(`${API}plant/`)
			return await response.json();
		},
	})

    const filtered = useMemo(() => {
        if (!Array.isArray(data)) return [];

        const q = String(search || "").trim().toLowerCase();

        return data.filter((p) => {
            const name = String(p?.name ?? "").toLowerCase();
            const plantCategory = String(p?.plant_category ?? "");
            const roles = rolesForPlant(p).map((role) => labelForRole(role).toLowerCase());
            const matchesCategory = !category || plantCategory === category;
            const matchesSearch =
                !q ||
                name.indexOf(q) !== -1 ||
                plantCategory.indexOf(q) !== -1 ||
                roles.some((role) => role.indexOf(q) !== -1);

            return matchesCategory && matchesSearch;
        });
        }, [data, search, category]);

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
                <Col xs={12} md={5}>
                <InputGroup>
                    <Form.Control
                    type="text"
                    placeholder="Search plants, roles, or labels..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    />
                </InputGroup>
                </Col>

                <Col xs={12} md={4} className="mt-2 mt-md-0">
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

                <Col xs={12} md={3} className="d-flex align-items-center mt-2 mt-md-0">
                <small className="selected-count">
                    Showing {filtered.length} of {data?.length ?? 0}
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
