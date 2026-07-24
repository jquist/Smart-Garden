import { Link } from "react-router-dom";

import Loading from "../components/Loading";
import { API } from "../constants";
import { useAuth } from "../auth/AuthContext";

const DEV_USERNAME = "dev_jquist";
const DEV_EMAIL = "jquist1234566@gmail.com";

function getBackendBaseUrl() {
  return String(API || "").replace(/\/api\/?$/, "");
}

function DevCommandBlock({ children }) {
  return (
    <pre className="dev-command-block">
      <code>{children}</code>
    </pre>
  );
}

function Dev() {
  const { user, loading } = useAuth();
  const backendBaseUrl = getBackendBaseUrl();
  const isDevUser = Boolean(user?.is_staff || user?.is_superuser);
  const liveAccountCommand =
    `python manage.py shell -c "from django.contrib.auth import get_user_model; ` +
    `User=get_user_model(); ` +
    `u, created=User.objects.get_or_create(username='${DEV_USERNAME}', defaults={'email':'${DEV_EMAIL}'}); ` +
    `u.email='${DEV_EMAIL}'; ` +
    `u.is_staff=True; u.is_superuser=True; u.is_active=True; ` +
    `u.set_password('PASTE_A_NEW_STRONG_PASSWORD_HERE'); ` +
    `u.save(); print('created' if created else 'updated')"`;

  if (loading) return <Loading message="Checking account..." />;

  if (!user) {
    return (
      <div className="dev-page">
        <header className="page-header">
          <div>
            <p className="page-kicker">Dev</p>
            <h1 className="page-title">Log in with a dev account.</h1>
            <p className="page-subtitle">
              This page is only for staff/admin accounts.
            </p>
          </div>
        </header>

        <div className="empty-state account-empty">
          Use the top bar to log in first.
        </div>
      </div>
    );
  }

  if (!isDevUser) {
    return (
      <div className="dev-page">
        <header className="page-header">
          <div>
            <p className="page-kicker">Dev</p>
            <h1 className="page-title">This account is not a dev account.</h1>
            <p className="page-subtitle">
              Ask an existing admin to mark your account as staff before using dev tools.
            </p>
          </div>
        </header>

        <div className="empty-state account-empty">
          Signed in as {user.username}, but staff/admin access is not enabled.
        </div>
      </div>
    );
  }

  return (
    <div className="dev-page">
      <header className="page-header">
        <div>
          <p className="page-kicker">Dev</p>
          <h1 className="page-title">Developer dashboard.</h1>
          <p className="page-subtitle">
            Quick checks, admin links, and safe live-account setup notes for the garden planner.
          </p>
        </div>
        <div className="selected-count">Admin access</div>
      </header>

      <div className="dev-grid">
        <section className="account-panel">
          <h2>Signed in</h2>
          <dl className="dev-detail-list">
            <div>
              <dt>Username</dt>
              <dd>{user.username}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user.email || "No email set"}</dd>
            </div>
            <div>
              <dt>Staff</dt>
              <dd>{user.is_staff ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Superuser</dt>
              <dd>{user.is_superuser ? "Yes" : "No"}</dd>
            </div>
          </dl>
        </section>

        <section className="account-panel">
          <h2>Quick links</h2>
          <div className="dev-link-grid">
            <a href={`${backendBaseUrl}/admin/`} className="btn btn-success">
              Django admin
            </a>
            <a href={`${backendBaseUrl}/api/plant/`} className="btn btn-outline-primary">
              Plant API
            </a>
            <a href={`${backendBaseUrl}/api/plant-summary/`} className="btn btn-outline-primary">
              Plant summary
            </a>
            <Link to="/projects" className="btn btn-outline-success">
              Projects
            </Link>
          </div>
        </section>

        <section className="account-panel dev-panel-wide">
          <h2>Make a dev account on Render</h2>
          <p>
            Run one of these commands in the Render backend shell. Use a new strong password for live, not a shared test password.
          </p>

          <h3>Simple interactive setup</h3>
          <DevCommandBlock>python manage.py createsuperuser</DevCommandBlock>

          <h3>Update this exact dev account</h3>
          <DevCommandBlock>{liveAccountCommand}</DevCommandBlock>
        </section>

        <section className="account-panel dev-panel-wide">
          <h2>Live safety checklist</h2>
          <div className="dev-check-grid">
            <span>Backend Render service has `DEBUG=False`.</span>
            <span>`SECRET_KEY` is generated in Render, not copied from local dev.</span>
            <span>`DATABASE_URL` points to the live Postgres database.</span>
            <span>`ALLOWED_HOSTS` includes the Render backend domain.</span>
            <span>`CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` include the live frontend domain.</span>
            <span>`SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` are set for HTTPS.</span>
            <span>Frontend has `REACT_APP_API_URL=https://your-render-service.onrender.com/api/`.</span>
            <span>After changing env vars, redeploy or restart the service.</span>
          </div>
        </section>
      </div>
    </div>
  );
}

export default Dev;
