import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import Loading from "../components/Loading";
import { useAuth } from "../auth/AuthContext";

function Profile() {
  const {
    user,
    loading,
    updateProfile,
    changePassword,
    logout,
  } = useAuth();
  const [profileForm, setProfileForm] = useState({ username: "", email: "" });
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [profileMessage, setProfileMessage] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    setProfileForm({
      username: user.username || "",
      email: user.email || "",
    });
  }, [user]);

  function updateProfileField(field, value) {
    setProfileForm((prev) => ({ ...prev, [field]: value }));
  }

  function updatePasswordField(field, value) {
    setPasswordForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleProfileSubmit(event) {
    event.preventDefault();
    setProfileSaving(true);
    setProfileMessage("");

    try {
      await updateProfile(profileForm);
      setProfileMessage("Profile updated.");
    } catch (error) {
      setProfileMessage(error.message);
    } finally {
      setProfileSaving(false);
    }
  }

  async function handlePasswordSubmit(event) {
    event.preventDefault();
    setPasswordSaving(true);
    setPasswordMessage("");

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordMessage("New passwords do not match.");
      setPasswordSaving(false);
      return;
    }

    try {
      await changePassword(passwordForm);
      setPasswordMessage("Password updated.");
      setPasswordForm({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    } catch (error) {
      setPasswordMessage(error.message);
    } finally {
      setPasswordSaving(false);
    }
  }

  if (loading) return <Loading message="Checking account..." />;

  if (!user) {
    return (
      <div className="profile-page">
        <header className="page-header">
          <div>
            <p className="page-kicker">Profile</p>
            <h1 className="page-title">Log in to manage your account.</h1>
            <p className="page-subtitle">
              Use the top bar to log in or sign up, then your profile and saved projects will appear here.
            </p>
          </div>
        </header>

        <div className="empty-state account-empty">
          Account tools are available once you are logged in.
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <header className="page-header">
        <div>
          <p className="page-kicker">Profile</p>
          <h1 className="page-title">Your account.</h1>
          <p className="page-subtitle">
            Manage your details, change your password, and jump back into saved garden projects.
          </p>
        </div>
        <div className="selected-count">{user.username}</div>
      </header>

      <div className="profile-grid">
        <section className="account-panel">
          <h2>Profile details</h2>
          <form onSubmit={handleProfileSubmit} className="account-form">
            <label className="auth-field">
              <span>Username</span>
              <input
                type="text"
                className="form-control"
                value={profileForm.username}
                onChange={(event) => updateProfileField("username", event.target.value)}
                autoComplete="username"
                required
              />
            </label>

            <label className="auth-field">
              <span>Email</span>
              <input
                type="email"
                className="form-control"
                value={profileForm.email}
                onChange={(event) => updateProfileField("email", event.target.value)}
                autoComplete="email"
              />
            </label>

            {profileMessage && (
              <div className="alert alert-info py-2 small mb-0">{profileMessage}</div>
            )}

            <button type="submit" className="btn btn-success" disabled={profileSaving}>
              {profileSaving ? "Saving..." : "Save profile"}
            </button>
          </form>
        </section>

        <section className="account-panel">
          <h2>Password</h2>
          <form onSubmit={handlePasswordSubmit} className="account-form">
            <label className="auth-field">
              <span>Current password</span>
              <input
                type="password"
                className="form-control"
                value={passwordForm.currentPassword}
                onChange={(event) => updatePasswordField("currentPassword", event.target.value)}
                autoComplete="current-password"
                required
              />
            </label>

            <label className="auth-field">
              <span>New password</span>
              <input
                type="password"
                className="form-control"
                value={passwordForm.newPassword}
                onChange={(event) => updatePasswordField("newPassword", event.target.value)}
                autoComplete="new-password"
                required
              />
            </label>

            <label className="auth-field">
              <span>Confirm new password</span>
              <input
                type="password"
                className="form-control"
                value={passwordForm.confirmPassword}
                onChange={(event) => updatePasswordField("confirmPassword", event.target.value)}
                autoComplete="new-password"
                required
              />
            </label>

            {passwordMessage && (
              <div className="alert alert-info py-2 small mb-0">{passwordMessage}</div>
            )}

            <button type="submit" className="btn btn-success" disabled={passwordSaving}>
              {passwordSaving ? "Updating..." : "Change password"}
            </button>
          </form>
        </section>

        <section className="account-panel account-panel-actions">
          <h2>Garden workspace</h2>
          <p>
            Saved planners are connected to this account, so project changes stay with the same login.
          </p>
          <Link to="/projects" className="btn btn-outline-primary">
            View projects
          </Link>
          <Link to="/canvas" className="btn btn-outline-success">
            New garden
          </Link>
          <button type="button" className="btn btn-outline-danger" onClick={logout}>
            Log out
          </button>
        </section>
      </div>
    </div>
  );
}

export default Profile;
