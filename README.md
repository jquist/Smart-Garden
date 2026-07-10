# Smart Garden Planner

Smart Garden Planner is a full-stack garden planning web application built with React and Django. It allows users to view plant data, check planting schedules, create garden boxes, add plants to a canvas, lock plant positions, and automatically arrange layouts using different solver options.

The system includes:

- a Django backend
- a React frontend
- a plant database
- a scheduler
- a drag-and-drop garden canvas
- Quick, Medium, and Slow autosort solver modes
- companion planting and avoid-plant rules

---

## Running the Project with Docker

Docker is the recommended way to run the project because it starts both the Django backend and React frontend together.

From the project root, run:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:3000
```

The Django backend runs inside Docker on port `8000`, and the React frontend runs through Nginx on port `3000`.

To stop the project:

```bash
docker compose down
```

To rebuild the backend after dependency or Docker changes:

```bash
docker compose build --no-cache backend
docker compose up
```

---

## Manual Local Development Setup

The project can also be run manually without Docker.

---

## Backend Setup

Create and activate a Python virtual environment.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / University Machines

```bash
python -m venv venv
source venv/bin/activate
```

Install backend dependencies:

```bash
cd django-app
pip install -r requirement.txt
```

Apply migrations and seed the database:

```bash
python manage.py makemigrations Plant_plotter
python manage.py migrate
python manage.py seed
```

Run the backend:

```bash
python manage.py runserver
```

The backend will run at:

```text
http://127.0.0.1:8000/
```

---

## Frontend Setup

Open a second terminal and run:

```bash
cd react-app
npm install
npm start
```

The frontend will run at:

```text
http://localhost:3000/
```

---

## Useful Django Commands

Create an admin user:

```bash
python manage.py createsuperuser
```

Clear the database:

```bash
python manage.py flush
```

Re-seed the plant database:

```bash
python manage.py seed
```

Run the solver benchmark:

```bash
python manage.py solver_benchmark
```

---

## Running Tests

Run the main test suite:

```bash
cd django-app
python manage.py test Plant_plotter -v 2
```

Run individual test files:

```bash
python manage.py test Plant_plotter.tests.test_solver_extra_regressions -v 2
python manage.py test Plant_plotter.tests.test_views_api -v 2
python manage.py test Plant_plotter.tests.test_predefined_scores -v 2
python manage.py test Plant_plotter.tests.test_solver_rules -v 2
python manage.py test Plant_plotter.tests.test_solver_comparison -v 2
```

Run stress tests:

```bash
python manage.py test Plant_plotter.tests.stress -v 2
```

---

## Benchmarking

Run the solver benchmark with:

```bash
python manage.py solver_benchmark
```

The benchmark is used to compare solver behaviour, runtime, placement success, and scoring across different layout scenarios.

---

## Docker Files

The Docker setup uses:

```text
docker-compose.yml
django-app/Dockerfile
react-app/Dockerfile
react-app/nginx.conf
```

The backend container runs Django with Gunicorn. The frontend container builds the React app and serves it with Nginx.

---

## Notes

- One grid square represents 15cm by 15cm.
- The canvas supports multiple garden boxes.
- Plants can be locked so the solver preserves their position.
- The autosort system supports Quick, Medium, and Slow solver modes.
- Max spread, avoid spacing, force row, force column, and companion overlap options can change the generated layout.
- Large layouts and optimal search may take longer to solve.
- The Django warnings about `related_name has no effect on ManyToManyField with a symmetrical relationship` do not stop the project from running.
