import { Col, Container, Row } from 'react-bootstrap';

function NotFound(props) {

	const { message } = props;

	return (
		<Container fluid className="vh-100 d-flex justify-content-center align-items-center">
			<Row>
				<Col className="text-center">
					<h1>Error</h1>
					<h2>{message}</h2>
				</Col>
			</Row>
		</Container>
	);
}

export default NotFound;
