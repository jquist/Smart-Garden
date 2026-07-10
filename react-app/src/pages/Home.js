
import { Col, Container, Row } from "react-bootstrap";



function Home() {
	return (
		
			<Container>
			<h1 className="text-center fw-bold display-3 mb-5 text-success">
				Smart Garden Planner
			</h1>
			<Row className="g-3">
			<Col xs={12} md={4}>
				<a className="btn btn-success w-100 py-3" href="/database">Database</a>
			</Col>
			<Col xs={12} md={4}>
				<a className="btn btn-success w-100 py-3" href="/scheduler">Scheduler</a>
			</Col>
			<Col xs={12} md={4}>
				<a className="btn btn-success w-100 py-3" href="/canvas">Canvas</a>
			</Col>
			</Row>

			</Container>

	);
}

export default Home;

