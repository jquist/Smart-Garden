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

function Database() {
    const [search, setSearch] = useState("");

	const { isPending, data, error } = useQuery({
		queryKey: ['plantData'],
		queryFn: async () => {
			const response = await fetch(`${API}plant/`)
			return await response.json();
		},
	})

    const filtered = useMemo(() => {
        if (!Array.isArray(data)) return [];

        const q = String(search||"").trim().toLowerCase();
        if (!q) return data;
        
        return data.filter((p) => {
            const name = String(p?.name ?? "").toLowerCase();
            return name.indexOf(q) !== -1;
        });
        }, [data,search]);

	if (isPending) return <Loading message="Loading..." />


	if (error) return <Error message="Could not load Plant" />

	return (
		<Container>
            {/* Search bar */}
            <Row className="mb-3">
                <Col xs={12} md={6}>
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

                <Col xs={12} md={6} className="d-flex align-items-center mt-2 mt-md-0">
                <small className="text-muted">
                    Showing {filtered.length} of {data?.length ?? 0}
                </small>
                </Col>
            </Row>
                    {/* Plant cards */}
            <Row className="g-3">
            {filtered.map((b) => (
                <Col key={b.id} xs={12} md={4}>
                <Plant data={b} />
                </Col>
            ))} 
            </Row>
		</Container>
	);
}

export default Database;

