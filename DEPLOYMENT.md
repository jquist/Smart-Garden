# Smart Garden Deployment Guide

Production shape:

```text
Vercel React frontend -> Render Django backend -> Supabase Postgres database
```

## 1. Push the prepared code

Commit and push the repository to GitHub before creating the hosted services.

The project is prepared for deployment with:

- `render.yaml` for the Render backend
- `react-app/vercel.json` for React app routing
- `django-app/.env.example` for backend environment variables
- `react-app/.env.example` for frontend environment variables

## 2. Create the Supabase database

1. Create a new Supabase project.
2. Open the project dashboard.
3. Click `Connect`.
4. Copy the Postgres connection string.
5. Use the session pooler connection string if Render cannot reach the direct IPv6 database URL.
6. Replace `[YOUR-PASSWORD]` with the real database password.
7. URL-encode special characters in the password if needed.

The value will be used as Render's `DATABASE_URL`.

## 3. Deploy the Django backend on Render

Recommended option: use the included `render.yaml`.

1. Open Render.
2. Choose `New` -> `Blueprint`.
3. Connect the GitHub repository.
4. Render should detect `render.yaml`.
5. Create the service.
6. In the Render service environment variables, set:

```env
DATABASE_URL=your-supabase-postgres-connection-string
ALLOWED_HOSTS=your-render-service.onrender.com
CORS_ALLOWED_ORIGINS=https://your-vercel-site.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-vercel-site.vercel.app
```

Render will generate `SECRET_KEY` automatically from `render.yaml`.

The configured backend build command is:

```bash
pip install -r requirement.txt && python manage.py collectstatic --noinput
```

The configured backend start command is:

```bash
python manage.py migrate && python manage.py seed --skip-if-plants-exist && gunicorn Plant_plotter_settings.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 180
```

After deployment, test:

```text
https://your-render-service.onrender.com/api/plant/
```

## 4. Deploy the React frontend on Vercel

1. Open Vercel.
2. Choose `Add New` -> `Project`.
3. Import the GitHub repository.
4. Set the root directory to:

```text
react-app
```

5. Use the Create React App/default React build settings:

```text
Build Command: npm run build
Output Directory: build
```

6. Add this Vercel environment variable:

```env
REACT_APP_API_URL=https://your-render-service.onrender.com/api/
```

7. Deploy.

## 5. Connect the final Vercel URL back to Render

Once Vercel gives you the final frontend URL, update the Render backend environment variables:

```env
CORS_ALLOWED_ORIGINS=https://your-final-vercel-site.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-final-vercel-site.vercel.app
```

Redeploy or restart the Render service after changing environment variables.

## 6. Add a custom domain

1. Buy the domain from a registrar.
2. Add the domain in the Vercel project settings.
3. Follow Vercel's DNS instructions.
4. After the domain works, update Render again:

```env
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

If you keep both the Vercel preview domain and custom domain active, include both values separated by commas.
