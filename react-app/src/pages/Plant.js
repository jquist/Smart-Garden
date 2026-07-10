/**
 * @todo
 * this will be a page that will display a single plant
 */
import { useQuery } from '@tanstack/react-query';
import { Col, Container, Row } from 'react-bootstrap';
import { useParams } from 'react-router-dom';
import Error from '../components/Error';
import { API } from '../constants';
import Breadcrumb from 'react-bootstrap/Breadcrumb';

function Plant() {
	const { id } = useParams();
	const plantQuery = useQuery({
	queryKey: ["plantData", id],
	queryFn: async () => {
		const res = await fetch(`${API}plant/${id}/`);
		if (!res.ok) throw new Error("Failed to load plant");
		return res.json();
	},
	});

	const helpsQuery = useQuery({
	queryKey: ["companion_helps_Data", id],
	queryFn: async () => {
		const res = await fetch(`${API}help/?plant=${id}`);
		if (!res.ok) throw new Error("Failed to load companion helps");
		return res.json();
	},
	});
	const helpsByQuery = useQuery({
	queryKey: ["companion_helps_By_Data", id],
	queryFn: async () => {
		const res = await fetch(`${API}help_by/?plant=${id}`);
		if (!res.ok) throw new Error("Failed to load companion helps");
		return res.json();
	},
	});
	const avoidsQuery = useQuery({
	queryKey: ["companion_avoid_Data", id],
	queryFn: async () => {
		const res = await fetch(`${API}avoid/?plant=${id}`);
		if (!res.ok) throw new Error("Failed to load companion helps");
		return res.json();
	},
	});

	
	const data = plantQuery.data;
	const companionHelps = helpsQuery.data;
	const companionHelpsby = helpsByQuery.data;
	const companionAvoids = avoidsQuery.data;

	const helpsList = Array.isArray(companionHelps)
	? companionHelps
	: companionHelps?.results ?? [];

	const helpsBYList = Array.isArray(companionHelpsby)
	? companionHelpsby
	: companionHelpsby?.results ?? [];

	const avoidList = Array.isArray(companionAvoids)
	? companionAvoids
	: companionAvoids?.results ?? [];
	


	return (
		<Container fluid>
			<Breadcrumb>
			  <Breadcrumb.Item href="/database">plants</Breadcrumb.Item>
			  <Breadcrumb.Item active>{data?.name}</Breadcrumb.Item>


			</Breadcrumb>
		  
			<Row>
				<Col md="auto">
				</Col>
				<Col>
					<h1>{data?.name}</h1>
					<p>plant_directly: {data?.plant_directly}</p>
					<p>Spacing between rows: {data?.spacing_between_rows}</p>
					<p>Spacing in the rows: {data?.spacing_in_rows}</p>
					<p>How deep does the seed need to be planted: {data?.depth}</p>
					<p>what is the first month of germination indoors?: {data?.time_to_germinate_indoors_start}</p>
					<p>what is the last month of germination indoors?: {data?.time_to_germinate_indoors_end}</p>
					<p>how long does it take to germinate before planting outside?: {data?.time_to_germinate_indoors_period}</p>
					<p>when is th efirst month you can start planting: {data?.plant_start}</p>
					<p>When is the last month you can plant it: {data?.plant_end}</p>
					<p>How long to first harvest: {data?.time_first_harvets}</p>
					<p>When does the harvest season start: {data?.harest_start}</p>
					<p>When does the harvest season end: {data?.harest_end}</p>
					

				</Col>
			</Row>
			<Row>
				<Col><h3>Compaion plants that help</h3></Col>
				<p>
				{helpsList.map((t, index) => (
				<div key={t.id}>
					{index + 1}. {t.other_plant_name}
				</div>
				))}
				</p>	
			</Row>
			<p></p>
			<Row>
				<Col><h3>Compaion plants that are helped by</h3></Col>
				<p>
				{helpsBYList.map((t, index) => (
				<div key={t.id}>
					{index + 1}. {t.other_plant_name}
				</div>
				))}
				</p>	
			</Row>
			<p></p>
			<Row>
				<Col><h3>Compaion plants that needs to be avoided</h3></Col>
				<p>
				{avoidList.map((t, index) => (
				<div key={t.id}>
					{index + 1}. {t.other_plant_name}
				</div>
				))}
				</p>	
			</Row>
		</Container>
	)
}

export default Plant;
