import { Link } from "react-router-dom";

function Home() {
	return (
		<div className="home-page">
			<header className="home-hero home-hero-detailed">
				<div className="home-hero-content">
					<p className="page-kicker">Free garden planning website</p>
					<h1 className="home-title">Plan your garden before anything goes in the soil.</h1>
					<p className="home-subtitle">
						Smart Garden Planner helps you choose plants, understand spacing, find helpful companions,
						build a simple garden layout, and check when each crop should be planted or harvested.
					</p>

					<div className="hero-actions" aria-label="Quick actions">
						<Link className="btn btn-success btn-lg" to="/canvas">
							Start my garden plan
						</Link>
						<Link className="btn btn-light btn-lg" to="/weed-control">
							Plan weed control
						</Link>
						<Link className="btn btn-light btn-lg" to="/database">
							Explore the plant guide
						</Link>
					</div>

					<div className="hero-note">
						Use it for raised beds, school gardens, small vegetable patches, allotments, or a first try at growing food.
					</div>
				</div>

				<aside className="planner-preview" aria-label="Garden planner preview">
					<div className="preview-topline">
						<span>Garden Bed A</span>
						<strong>15cm grid</strong>
					</div>
					<div className="preview-grid">
						<span className="crop crop-tomato">Tomato</span>
						<span className="crop crop-basil">Basil</span>
						<span className="crop crop-carrot">Carrot</span>
						<span className="crop crop-lettuce">Lettuce</span>
						<span className="crop crop-marigold">Marigold</span>
					</div>
					<div className="preview-list">
						<div>
							<strong>Good neighbours</strong>
							<span>Basil may help tomato</span>
						</div>
						<div>
							<strong>Spacing check</strong>
							<span>Plants use their real size</span>
						</div>
						<div>
							<strong>Calendar</strong>
							<span>See sowing and harvest windows</span>
						</div>
					</div>
				</aside>
			</header>

			<section className="home-section intro-section">
				<div className="section-heading section-heading-wide">
					<p className="page-kicker">What this website does</p>
					<h2>It brings the messy parts of garden planning into one easy place.</h2>
					<p>
						Planning a garden can mean checking seed packets, drawing beds on paper, searching plant spacing,
						looking up companion planting, and trying to remember which month each plant belongs in.
						This website puts those jobs together so the plan is easier to understand.
					</p>
				</div>

				<div className="feature-grid" aria-label="Smart Garden Planner features">
					<div className="feature-card">
						<h3>Visual bed planner</h3>
						<p>Draw garden boxes, place plants on a grid, move them around, and see what fits before planting day.</p>
					</div>
					<div className="feature-card">
						<h3>Plant guide</h3>
						<p>Search plants by name or type and read simple information such as spacing, category, and useful labels.</p>
					</div>
					<div className="feature-card">
						<h3>Companion ideas</h3>
						<p>Check which plants may help each other and which plants are better kept apart in the garden.</p>
					</div>
					<div className="feature-card">
						<h3>Growing calendar</h3>
						<p>Compare sowing, planting, and harvest windows so your layout also makes sense through the year.</p>
					</div>
					<div className="feature-card">
						<h3>Autosort help</h3>
						<p>Let the planner try a tidy arrangement when a bed gets crowded or hard to organise by hand.</p>
					</div>
					<div className="feature-card">
						<h3>Beginner friendly</h3>
						<p>Use plain buttons, clear labels, and step-by-step pages instead of needing gardening knowledge first.</p>
					</div>
				</div>
			</section>

			<section className="home-section">
				<div className="section-heading">
					<p className="page-kicker">How to use it</p>
					<h2>A simple path from idea to garden plan.</h2>
					<p>
						Start anywhere, but this order works well if you are new.
					</p>
				</div>

				<div className="guide-grid" aria-label="Website overview">
					<div className="guide-card">
						<span className="guide-number">1</span>
						<h3>Choose what you want to grow</h3>
						<p>Open the plant guide and search for vegetables, herbs, weeds, flowers, or other plant types.</p>
					</div>
					<div className="guide-card">
						<span className="guide-number">2</span>
						<h3>Build your garden space</h3>
						<p>Open the garden planner, add a square or rectangle bed, then place plants into the space.</p>
					</div>
					<div className="guide-card">
						<span className="guide-number">3</span>
						<h3>Improve the layout</h3>
						<p>Use companion recommendations, lock favourite positions, and try autosort for a cleaner design.</p>
					</div>
					<div className="guide-card">
						<span className="guide-number">4</span>
						<h3>Check the months</h3>
						<p>Use the growing calendar to understand when plants can be started, moved outside, and harvested.</p>
					</div>
				</div>
			</section>

			<section className="home-section example-section">
				<div className="example-story">
					<div>
						<p className="page-kicker">Example</p>
						<h2>Say you want tomatoes, basil, and carrots.</h2>
						<p>
							You can search each plant, place them into a bed, check if any companion relationships help,
							and then look at the calendar to see whether the timing works. If the layout feels messy,
							the garden planner can try arranging the plants for you.
						</p>
					</div>
					<div className="example-steps">
						<span>Search plants</span>
						<span>Add them to a bed</span>
						<span>Refresh companion ideas</span>
						<span>Check planting months</span>
					</div>
				</div>
			</section>

			<section className="home-section start-section">
				<div className="section-heading">
					<p className="page-kicker">Choose where to go</p>
					<h2>Each part of the website answers a different gardening question.</h2>
				</div>

				<div className="home-actions" aria-label="Main tools">
					<Link className="action-card action-card-primary" to="/canvas">
						<div>
							<span className="action-label">Where should things go?</span>
							<h3>Garden planner</h3>
							<p>Use this when you want to draw beds, add plants, drag crops around, and test a layout.</p>
						</div>
						<span className="action-link">Open garden planner</span>
					</Link>

					<Link className="action-card" to="/weed-control">
						<div>
							<span className="action-label">What handles my weeds?</span>
							<h3>Weed control canvas</h3>
							<p>Use this when you want to map weeds first, then add plants chosen only for weed control.</p>
						</div>
						<span className="action-link">Open weed control</span>
					</Link>

					<Link className="action-card" to="/database">
						<div>
							<span className="action-label">What is this plant like?</span>
							<h3>Plant guide</h3>
							<p>Use this when you want plant information before deciding what belongs in your garden.</p>
						</div>
						<span className="action-link">Browse plant guide</span>
					</Link>

					<Link className="action-card" to="/scheduler">
						<div>
							<span className="action-label">When should I plant it?</span>
							<h3>Growing calendar</h3>
							<p>Use this when you want to compare planting and harvest windows across the year.</p>
						</div>
						<span className="action-link">View growing calendar</span>
					</Link>
				</div>
			</section>

			<section className="home-section friendly-section">
				<div className="friendly-panel">
					<div>
						<p className="page-kicker">For all ages</p>
						<h2>Made to be understandable, not intimidating.</h2>
						<p>
							The website works for beginners, children learning about plants, families planning together,
							and gardeners who want a clearer plan before planting.
						</p>
					</div>
					<ul className="friendly-list">
						<li>Plain labels explain what each tool is for.</li>
						<li>The grid makes spacing easier to see.</li>
						<li>You can experiment without ruining a real garden bed.</li>
						<li>The calendar helps turn a layout into a seasonal plan.</li>
					</ul>
				</div>
			</section>
		</div>

	);
}

export default Home;
