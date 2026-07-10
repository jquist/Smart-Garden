import 'bootstrap/dist/css/bootstrap.min.css';
import { Container, Navbar} from 'react-bootstrap';
import { Link, Outlet } from 'react-router-dom';


function MainLayout({ children }) {
	return (
		<div>
			<Navbar bg="dark" variant="dark" className='p-3'>

					
					<Navbar.Brand as={Link} to="/" className="text-white text-decoration-none">
						Plant plotter
					</Navbar.Brand>
					<Navbar.Brand as={Link} to="/database" className="text-white text-decoration-none">
						Database
					</Navbar.Brand>
					<Navbar.Brand as={Link} to="/Scheduler" className="text-white text-decoration-none">
						Scheduler
					</Navbar.Brand>
					<Navbar.Brand as={Link} to="/Canvas" className="text-white text-decoration-none">
						Canvas
					</Navbar.Brand>
					

			</Navbar>
			<Container fluid className="mt-4">
				<Outlet />
			</Container>

		</div>
	);
}

export default MainLayout;
