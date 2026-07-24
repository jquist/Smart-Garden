import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Navbar} from 'react-bootstrap';
import { NavLink, Outlet } from 'react-router-dom';


function MainLayout({ children }) {
	return (
		<div className="app-shell">
			<header className="site-header">
				<div className="garden-strip">
					<Container fluid className="px-3 px-lg-4">
						<span>Plan your beds, learn your plants, grow with confidence</span>
					</Container>
				</div>

			<Navbar expand="md" className="app-navbar py-3">
				<Container fluid className="px-3 px-lg-4 align-items-center">
					<NavLink to="/" className="brand-lockup text-decoration-none">
						<span className="brand-mark">
							<img src="/logo192.png" alt="" />
						</span>
						<span>
							Smart Garden Planner
							<span className="brand-subtitle">A friendly guide for every grower</span>
						</span>
					</NavLink>

					<nav className="app-nav ms-md-auto" aria-label="Primary navigation">
						<NavLink to="/" end className="app-nav-link">
							Home
						</NavLink>
						<NavLink to="/database" className="app-nav-link">
							Plant guide
						</NavLink>
						<NavLink to="/scheduler" className="app-nav-link">
							Growing calendar
						</NavLink>
						<NavLink to="/canvas" className="app-nav-link">
							Garden planner
						</NavLink>
					</nav>
				</Container>
			</Navbar>
			</header>

			<Container fluid as="main" className="app-content">
				<Outlet />
			</Container>
		</div>
	);
}

export default MainLayout;
