import { Col, Container, Row } from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';

function Loading(props) {
	return (
		<Container fluid className="vh-100 d-flex justify-content-center align-items-center">
			<Row>
				<Col className="text-center loading-card">
					<Spinner animation="border" role="status">

					</Spinner>
					<p>{props.message}</p>
				</Col>
			</Row>
		</Container>
	);
}

export default Loading;
