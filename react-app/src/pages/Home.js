import { Link } from "react-router-dom";



function Home() {
	return (
		<div>
			<header className="page-header">
				<div>
					<p className="page-kicker">Garden planning</p>
					<h1 className="page-title">Design a productive garden with fewer tradeoffs.</h1>
					<p className="page-subtitle">
						Plan beds, compare companion relationships, and map planting windows in one focused workspace.
					</p>
				</div>
			</header>

			<section className="metric-row" aria-label="Workspace highlights">
				<div className="metric">
					<span className="metric-value">15cm</span>
					<span className="metric-label">Grid precision for plant spacing</span>
				</div>
				<div className="metric">
					<span className="metric-value">3</span>
					<span className="metric-label">Solver modes for layout planning</span>
				</div>
				<div className="metric">
					<span className="metric-value">12</span>
					<span className="metric-label">Months visible in the schedule</span>
				</div>
			</section>

			<section className="home-actions" aria-label="Main tools">
				<Link className="action-card" to="/canvas">
					<div>
						<h2>Plan the canvas</h2>
						<p>Create beds, place crops, lock important decisions, and run autosort when the layout gets crowded.</p>
					</div>
					<span>Open canvas</span>
				</Link>

				<Link className="action-card" to="/database">
					<div>
						<h2>Review plants</h2>
						<p>Search the plant database by crop, category, and role before deciding what belongs in the garden.</p>
					</div>
					<span>Browse database</span>
				</Link>

				<Link className="action-card" to="/scheduler">
					<div>
						<h2>Check the schedule</h2>
						<p>See sowing, planting, and harvest windows so the garden plan matches the season.</p>
					</div>
					<span>View schedule</span>
				</Link>
			</section>
		</div>

	);
}

export default Home;

