# Smart Garden Detailed Deployment Guide

Production shape:

```text
Vercel React frontend -> Render Django backend -> Supabase Postgres database
```

Suggested public name:

```text
PlotPatch
```

Suggested domains to check:

```text
plotpatch.app
plotpatch.com
plotpatch.garden
```

## 0. Before you start

You need accounts for:

- GitHub
- Supabase
- Render
- Vercel

Make sure the latest code is committed and pushed to GitHub.

From this project root, the important deployment files are:

```text
render.yaml
django-app/requirement.txt
django-app/.env.example
react-app/vercel.json
react-app/.env.example
```

Do not upload real `.env` files or passwords to GitHub.

## 1. Create the Supabase database

Supabase is only the database for this project. You are not deploying the React or Django app to Supabase.

1. Go to Supabase.
2. Sign in.
3. Click `New project`.
4. Choose your organization.
5. Project name:

```text
plotpatch
```

6. Set a database password.
7. Save that password somewhere private. You need it again for Render.
8. Choose a region close to your users.
9. Choose the free plan if this is coursework/testing.
10. Click `Create new project`.
11. Wait until Supabase finishes creating the project.

## 2. Get the Supabase database URL

1. Open your Supabase project.
2. Click `Connect`.
3. Choose a Postgres connection string.
4. For Render, prefer the `Session pooler` connection string if available.
5. Copy the connection string.

It will look roughly like this:

```text
postgres://postgres.PROJECT_REF:[YOUR-PASSWORD]@aws-0-region.pooler.supabase.com:5432/postgres
```

Replace:

```text
[YOUR-PASSWORD]
```

with your real Supabase database password.

Important:

- Use the database connection string, not the Supabase anon key.
- If your password has special characters like `@`, `#`, `%`, `/`, or `?`, URL-encode the password or reset it to a simpler long password.
- Keep the full connection string private.

You will paste this into Render as:

```env
DATABASE_URL=your-supabase-connection-string
```

## 3. Deploy the Django backend on Render

Render hosts your API/backend.

Recommended method: use the included `render.yaml`.

1. Go to Render.
2. Sign in.
3. Connect Render to your GitHub account if it asks.
4. Click `New`.
5. Click `Blueprint`.
6. Choose the GitHub repository for this project.
7. Choose the branch you pushed, usually:

```text
main
```

8. Render should detect:

```text
render.yaml
```

9. Confirm/create the Blueprint.
10. Render will create a web service named:

```text
smart-garden-api
```

11. Open the new Render service.
12. Go to `Environment`.
13. Add these environment variables.

Use your real Supabase value:

```env
DATABASE_URL=postgres://postgres.PROJECT_REF:YOUR_PASSWORD@aws-0-region.pooler.supabase.com:5432/postgres
```

Use your actual Render service domain:

```env
ALLOWED_HOSTS=your-render-service.onrender.com
```

For now, before Vercel exists, you can temporarily use:

```env
CORS_ALLOWED_ORIGINS=https://temporary-placeholder.vercel.app
CSRF_TRUSTED_ORIGINS=https://temporary-placeholder.vercel.app
```

Render should generate this automatically from `render.yaml`:

```env
SECRET_KEY=generated-by-render
```

This is already set in `render.yaml`:

```env
DEBUG=False
```

14. Save the environment variables.
15. Click `Manual Deploy`.
16. Click `Deploy latest commit`.
17. Wait for the build and deploy to finish.

The included Render build command is:

```bash
pip install -r requirement.txt && python manage.py collectstatic --noinput
```

The included Render start command is:

```bash
python manage.py migrate && python manage.py seed --skip-if-plants-exist && gunicorn Plant_plotter_settings.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 180
```

That command does three things:

- Creates the database tables in Supabase.
- Adds the plant seed data the first time.
- Starts the Django API.

## 4. Test the Render backend

When Render says the deploy is live, open:

```text
https://your-render-service.onrender.com/api/plant/
```

Expected result:

- You should see JSON data.
- Or you may see the Django REST Framework browsable API page.

If you get `DisallowedHost`, fix `ALLOWED_HOSTS`.

If you get a database/password error, fix `DATABASE_URL`.

If you get an empty plant list, open the Render shell and run:

```bash
python manage.py seed --skip-if-plants-exist
```

## 5. Deploy the React frontend on Vercel

Vercel hosts the visible website.

1. Go to Vercel.
2. Sign in.
3. Connect Vercel to your GitHub account if it asks.
4. Click `Add New`.
5. Click `Project`.
6. Choose the same GitHub repository.
7. In the project setup screen, set the root directory to:

```text
react-app
```

8. Make sure the framework is detected as Create React App or React.
9. Use these build settings:

```text
Build Command: npm run build
Output Directory: build
Install Command: npm install
```

10. Open the environment variables section.
11. Add:

```env
REACT_APP_API_URL=https://your-render-service.onrender.com/api/
```

12. Select at least `Production`.
13. Select `Preview` too if Vercel gives you the option.
14. Click `Deploy`.
15. Wait for Vercel to finish.
16. Open the Vercel URL.

It will look like:

```text
https://your-project-name.vercel.app
```

## 6. Connect Vercel back to Render

Now that you have the real Vercel URL, update the Render backend.

1. Go back to Render.
2. Open the `smart-garden-api` service.
3. Go to `Environment`.
4. Replace the temporary CORS values with your real Vercel URL:

```env
CORS_ALLOWED_ORIGINS=https://your-project-name.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-project-name.vercel.app
```

5. Save changes.
6. Redeploy or restart the Render service.
7. Refresh the Vercel site.

The frontend should now load plant data from the Render API.

## 7. Add a custom domain on Vercel

Do this after the Vercel site works on the `.vercel.app` URL.

1. Buy your domain from a registrar.
2. Good first choice:

```text
plotpatch.app
```

3. In Vercel, open your project.
4. Go to `Settings`.
5. Go to `Domains`.
6. Add your domain.
7. Follow the DNS instructions Vercel gives you.
8. Wait for DNS verification.
9. Open your custom domain in the browser.

If the custom domain is:

```text
https://plotpatch.app
```

then update Render again:

```env
CORS_ALLOWED_ORIGINS=https://plotpatch.app,https://your-project-name.vercel.app
CSRF_TRUSTED_ORIGINS=https://plotpatch.app,https://your-project-name.vercel.app
```

Then redeploy or restart Render.

## 8. Final testing checklist

Test these URLs:

```text
https://your-render-service.onrender.com/api/plant/
https://your-project-name.vercel.app
https://your-domain.com
```

On the website, check:

- Home page loads.
- Plant database page loads.
- Scheduler page loads.
- Canvas page loads.
- Autosort works.

## 9. Common problems

### Frontend loads but no plant data

Check Vercel:

```env
REACT_APP_API_URL=https://your-render-service.onrender.com/api/
```

Then redeploy Vercel.

### Render says DisallowedHost

Check Render:

```env
ALLOWED_HOSTS=your-render-service.onrender.com
```

No `https://` in `ALLOWED_HOSTS`.

### Browser says CORS error

Check Render:

```env
CORS_ALLOWED_ORIGINS=https://your-vercel-site.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-vercel-site.vercel.app
```

Use full `https://` URLs here.

### Database connection fails

Check:

- `DATABASE_URL` is the Supabase Postgres connection string.
- The password is correct.
- Special characters in the password are URL-encoded.
- You used the session pooler string if the direct connection does not work.

### Vercel page refresh gives 404

Make sure this file exists:

```text
react-app/vercel.json
```

It is already included in this project.
