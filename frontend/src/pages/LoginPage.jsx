import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { getProfile, loginUser } from "../api/client.js";
import ClickWordmark from "../components/ClickWordmark.jsx";
import { useSession } from "../context/SessionContext.jsx";

const initialForm = {
  email: "",
  password: ""
};

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { authNotice, consumeAuthNotice, isAuthenticated, login, setUser } = useSession();
  const [form, setForm] = useState(initialForm);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const redirectTo = location.state?.from?.pathname || "/";
  const registrationSuccess = location.state?.registrationSuccess || "";

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      const response = await loginUser(form);
      login(response?.data);

      try {
        const profile = await getProfile(response?.data?.tokens?.access_token);
        setUser(profile?.data || response?.data?.user || null);
      } catch {
        setUser(response?.data?.user || null);
      }

      navigate(redirectTo, { replace: true });
    } catch (requestError) {
      setError(requestError.message || "Unable to sign in.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="login-card form-shell auth-card-pro">
        <div className="auth-layout">
          <div className="auth-copy-block">
            <div className="auth-brand">
              <ClickWordmark className="click-wordmark-auth" />
            </div>
            <div className="auth-copy-stack">
              <p className="eyebrow">Sign in</p>
              <h1>Welcome back</h1>
              <p className="page-copy">Open Click and continue the work.</p>
            </div>
            <div className="auth-quick-points" aria-hidden="true">
              <span>Tasks</span>
              <span>Projects</span>
              <span>Inbox</span>
            </div>
          </div>

          <form className="form-shell auth-form-panel" onSubmit={handleSubmit}>
            {authNotice ? (
              <div className="warning-banner">
                {authNotice}
                <button type="button" className="link-button" onClick={consumeAuthNotice}>
                  Dismiss
                </button>
              </div>
            ) : null}

            {error ? <div className="error-banner">{error}</div> : null}
            {registrationSuccess ? <div className="success-banner">{registrationSuccess}</div> : null}

            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                className="text-input"
                value={form.email}
                onChange={handleChange}
                placeholder="you@example.com"
                required
              />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                className="text-input"
                value={form.password}
                onChange={handleChange}
                placeholder="••••••••••••"
                required
              />
            </div>

            <div className="toolbar-actions auth-actions-grid">
              <button type="submit" className="btn btn-primary" disabled={pending}>
                {pending ? "Signing in..." : "Sign in"}
              </button>
              <Link to="/register" className="btn btn-secondary">
                Create account
              </Link>
            </div>

            <div className="auth-subactions">
              <Link to="/forgot-password">Forgot password</Link>
              <Link to="/verify-email">Verify email</Link>
              <Link to="/dashboard">Preview</Link>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}