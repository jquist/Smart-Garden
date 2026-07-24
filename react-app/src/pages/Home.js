import { Link } from "react-router-dom";



function Home() {
	return (
		<div className="home-page">
			<header className="home-hero">
				<div className="home-hero-content">
					<p className="page-kicker">Welcome to your garden helper</p>
					<h1 className="home-title">Smart Garden Planner</h1>
					<p className="home-subtitle">
						A friendly website for planning where plants go, learning which plants grow well together,
						and choosing the right time to sow, plant, and harvest.
					</p>

					<div className="hero-actions" aria-label="Quick actions">
						<Link className="btn btn-success btn-lg" to="/canvas">
							Start planning
						</Link>
						<Link className="btn btn-light btn-lg" to="/database">
							Learn about plants
						</Link>
					</div>

					<div className="hero-note">
						Made for beginners, families, school projects, and gardeners who want a clearer plan.
					</div>
				</div>
			</header>

			<section className="home-section">
				<div className="section-heading">
					<p className="page-kicker">What this website helps with</p>
					<h2>Plan a garden one simple step at a time.</h2>
					<p>
						You do not need to know all the gardening rules before you begin. The website gives you
						places to explore, try ideas, and improve your plan as you learn.
					</p>
				</div>

				<div className="guide-grid" aria-label="Website overview">
					<div className="guide-card">
						<span className="guide-number">1</span>
						<h3>Pick plants</h3>
						<p>Search the plant guide, read simple labels, and find useful details like spacing and growing type.</p>
					</div>
					<div className="guide-card">
						<span className="guide-number">2</span>
						<h3>Place them in beds</h3>
						<p>Use the planner canvas to draw garden boxes, add crops, move them around, and see what fits.</p>
					</div>
					<div className="guide-card">
						<span className="guide-number">3</span>
						<h3>Check the season</h3>
						<p>Use the growing calendar to see planting and harvest windows across the year.</p>
					</div>
				</div>
			</section>

			<section className="home-section start-section">
				<div className="section-heading">
					<p className="page-kicker">Choose where to go</p>
					<h2>Start with the tool that matches your question.</h2>
				</div>

				<div className="home-actions" aria-label="Main tools">
				<Link className="action-card action-card-primary" to="/canvas">
					<div>
						<span className="action-label">Best first step</span>
						<h3>Garden planner</h3>
						<p>Build your garden bed layout, add plants, move crops around, and let autosort suggest a tidy plan.</p>
					</div>
					<span className="action-link">Open garden planner</span>
				</Link>

				<Link className="action-card" to="/database">
					<div>
						<span className="action-label">Learn first</span>
						<h3>Plant guide</h3>
						<p>Look up plants, see their labels, and understand basic details before adding them to your plan.</p>
					</div>
					<span className="action-link">Browse plant guide</span>
				</Link>

				<Link className="action-card" to="/scheduler">
					<div>
						<span className="action-label">Check timing</span>
						<h3>Growing calendar</h3>
						<p>Compare when plants can be started, planted outside, and harvested through the year.</p>
					</div>
					<span className="action-link">View growing calendar</span>
				</Link>
				</div>
			</section>

			<section className="home-section friendly-section">
				<div className="friendly-panel">
					<div>
						<p className="page-kicker">For all ages</p>
						<h2>Clear words, simple choices, and room to experiment.</h2>
						<p>
							The site is designed so a new gardener can understand what to do next, while a more
							confident gardener can still use the planner, companion suggestions, and calendar tools.
						</p>
					</div>
					<ul className="friendly-list">
						<li>Use plain search to find a plant by name or type.</li>
						<li>Try a layout without needing graph paper.</li>
						<li>See companion ideas when you already have plants on the canvas.</li>
						<li>Lock plants you want to keep in place before sorting.</li>
					</ul>
				</div>
			</section>
		</div>

	);
}

export default Home;

