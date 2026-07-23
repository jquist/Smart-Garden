/**
 * @todo
 * this will be a page that will display a single plant
 */
import { useQuery } from '@tanstack/react-query';
import { Col, Container, Row } from 'react-bootstrap';
import { useParams } from 'react-router-dom';
import { API } from '../constants';
import Breadcrumb from 'react-bootstrap/Breadcrumb';
import PlantBadges from '../components/PlantBadges';
import Error from '../components/Error';
import Loading from '../components/Loading';

function asList(data) {
	return Array.isArray(data) ? data : data?.results ?? [];
}

function displayValue(value, fallback = "Not set") {
	if (value === true) return "Yes";
	if (value === false) return "No";
	return value ?? fallback;
}

function RelationshipList({ items, emptyText }) {
	if (items.length === 0) {
		return <p className="text-muted">{emptyText}</p>;
	}

	return (
		<ul className="mb-0">
			{items.map((item) => (
				<li key={item.id}>{item.other_plant_name}</li>
			))}
		</ul>
	);
}

function NameList({ names, emptyText }) {
	if (!Array.isArray(names) || names.length === 0) {
		return <p className="text-muted">{emptyText}</p>;
	}

	return (
		<ul className="mb-0">
			{names.map((name) => (
				<li key={name}>{name}</li>
			))}
		</ul>
	);
}

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
		if (!res.ok) throw new Error("Failed to load companion avoids");
		return res.json();
	},
	});

	const data = plantQuery.data;
	const helpsList = asList(helpsQuery.data);
	const helpsByList = asList(helpsByQuery.data);
	const avoidList = asList(avoidsQuery.data);

	if (plantQuery.isPending) return <Loading message="Loading plant..." />;
	if (plantQuery.error) return <Error message="Could not load plant" />;

	const plantDetails = [
		["Direct sow", displayValue(data?.plant_directly)],
		["Spacing between rows", `${displayValue(data?.spacing_between_rows, 0)} cm`],
		["Spacing in rows", `${displayValue(data?.spacing_in_rows, 0)} cm`],
		["Seed depth", `${displayValue(data?.depth, 0)} cm`],
		["Indoor germination start", displayValue(data?.time_to_germinate_indoors_start)],
		["Indoor germination end", displayValue(data?.time_to_germinate_indoors_end)],
		["Indoor germination period", `${displayValue(data?.time_to_germinate_indoors_period, 0)} days`],
		["Planting start", displayValue(data?.plant_start)],
		["Planting end", displayValue(data?.plant_end)],
		["Days to first harvest", displayValue(data?.time_first_harvets, 0)],
		["Harvest start", displayValue(data?.harest_start)],
		["Harvest end", displayValue(data?.harest_end)],
	];

	return (
		<Container fluid className="px-0">
			<Breadcrumb>
			  <Breadcrumb.Item href="/database">Plants</Breadcrumb.Item>
			  <Breadcrumb.Item active>{data?.name}</Breadcrumb.Item>
			</Breadcrumb>

			<header className="page-header">
				<div>
					<p className="page-kicker">Plant profile</p>
					<h1 className="page-title">{data?.name}</h1>
					<PlantBadges plant={data} maxRoles={8} />
				</div>
			</header>

			<Row className="mb-4 content-panel">
				<Col md={8} lg={6}>
					<dl className="row detail-list g-3">
						{plantDetails.map(([label, value]) => (
							<div key={label} className="col-12 col-md-6">
								<dt>{label}</dt>
								<dd>{value}</dd>
							</div>
						))}
					</dl>
				</Col>
			</Row>

			<Row className="g-4">
				<Col md={4}>
					<div className="content-panel relationship-panel h-100">
					<h3>Plants that help this plant</h3>
					<RelationshipList
						items={helpsByList}
						emptyText="No reliable helper companions listed yet."
					/>
					</div>
				</Col>
				<Col md={4}>
					<div className="content-panel relationship-panel h-100">
					<h3>Plants this plant helps</h3>
					<RelationshipList
						items={helpsList}
						emptyText="No plants listed as helped by this one yet."
					/>
					</div>
				</Col>
				<Col md={4}>
					<div className="content-panel relationship-panel h-100">
					<h3>Plants to keep away</h3>
					<RelationshipList
						items={avoidList}
						emptyText="No avoid relationships listed."
					/>
					</div>
				</Col>
			</Row>

			{(data?.plant_category === "weed" || data?.weed_management_notes || data?.weed_suppressors?.length > 0) && (
				<Row className="g-4 mt-1">
					<Col md={6}>
						<div className="content-panel relationship-panel h-100">
							<h3>Weed control notes</h3>
							<p>{data?.weed_management_notes || "No weed control notes listed."}</p>
						</div>
					</Col>
					<Col md={6}>
						<div className="content-panel relationship-panel h-100">
							<h3>Useful suppressor plants</h3>
							<NameList
								names={data?.weed_suppressors}
								emptyText="No suppressor plants listed."
							/>
						</div>
					</Col>
				</Row>
			)}

			{data?.weeds_suppressed?.length > 0 && (
				<Row className="g-4 mt-1">
					<Col md={6}>
						<div className="content-panel relationship-panel h-100">
							<h3>Weeds this plant can suppress</h3>
							<NameList
								names={data?.weeds_suppressed}
								emptyText="No suppressed weeds listed."
							/>
						</div>
					</Col>
				</Row>
			)}
		</Container>
	)
}

export default Plant;
