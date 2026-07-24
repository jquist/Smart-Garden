import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

function AuthControls() {
  const { user, loading, login, signup, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function openAuth(nextMode) {
    setMode(nextMode);
    setMessage("");
    setOpen(true);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");

    try {
      if (mode === "login") {
        await login(form);
      } else {
        await signup(form);
      }
      setOpen(false);
      setForm({ username: "", email: "", password: "" });
    } catch (error) {
      setMessage(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <span className="auth-status">Checking account...</span>;
  }

  if (user) {
    return (
      <div className="auth-controls">
        <NavLink to="/profile" className="auth-status auth-status-link">
          {user.username}
        </NavLink>
        <button type="button" className="auth-button" onClick={logout}>
          Log out
        </button>
      </div>
    );
  }

  return (
    <>
      <div className="auth-controls">
        <button type="button" className="auth-button" onClick={() => openAuth("login")}>
          Log in
        </button>
        <button type="button" className="auth-button auth-button-primary" onClick={() => openAuth("signup")}>
          Sign up
        </button>
      </div>

      {open && (
        <div className="auth-modal-backdrop" role="dialog" aria-modal="true">
          <form className="auth-modal" onSubmit={handleSubmit}>
            <div className="auth-modal-header">
              <div>
                <p className="page-kicker">Account</p>
                <h2>{mode === "login" ? "Log in" : "Create account"}</h2>
              </div>
              <button type="button" className="workflow-modal-close" onClick={() => setOpen(false)} aria-label="Close">
                X
              </button>
            </div>

            <label className="auth-field">
              <span>Username</span>
              <input
                type="text"
                className="form-control"
                value={form.username}
                onChange={(event) => updateField("username", event.target.value)}
                autoComplete="username"
                required
              />
            </label>

            {mode === "signup" && (
              <label className="auth-field">
                <span>Email</span>
                <input
                  type="email"
                  className="form-control"
                  value={form.email}
                  onChange={(event) => updateField("email", event.target.value)}
                  autoComplete="email"
                />
              </label>
            )}

            <label className="auth-field">
              <span>Password</span>
              <input
                type="password"
                className="form-control"
                value={form.password}
                onChange={(event) => updateField("password", event.target.value)}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                required
              />
            </label>

            {message && <div className="alert alert-danger py-2 small mb-0">{message}</div>}

            <button type="submit" className="btn btn-success w-100" disabled={submitting}>
              {submitting ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
            </button>

            <button
              type="button"
              className="btn btn-link text-decoration-none"
              onClick={() => {
                setMode((prev) => (prev === "login" ? "signup" : "login"));
                setMessage("");
              }}
            >
              {mode === "login" ? "Need an account? Sign up" : "Already have an account? Log in"}
            </button>
          </form>
        </div>
      )}
    </>
  );
}

export default AuthControls;
