import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Navbar} from 'react-bootstrap';
import { NavLink, Outlet } from 'react-router-dom';


function MainLayout({ children }) {
	return (
		<div className="app-shell">
			<Navbar expand="md" className="app-navbar py-3">
				<Container fluid className="px-3 px-lg-4">
					<NavLink to="/" className="brand-lockup text-decoration-none">
						<span className="brand-mark">SG</span>
						<span>
							Smart Garden
							<span className="brand-subtitle">Planning workspace</span>
						</span>
					</NavLink>

					<nav className="app-nav ms-md-auto" aria-label="Primary navigation">
						<NavLink to="/" end className="app-nav-link">
							Home
						</NavLink>
						<NavLink to="/database" className="app-nav-link">
							Plants
						</NavLink>
						<NavLink to="/scheduler" className="app-nav-link">
							Schedule
						</NavLink>
						<NavLink to="/canvas" className="app-nav-link">
							Canvas
						</NavLink>
					</nav>
				</Container>
			</Navbar>

			<Container fluid as="main" className="app-content">
				<Outlet />
			</Container>
		</div>
	);
}

export default MainLayout;
