import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../api/client.js";
import ClickWordmark from "../components/ClickWordmark.jsx";

const initialForm = {
  first_name: "",
  last_name: "",
  email: "",
  password: "",
  confirmPassword: ""
};

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setPending(true);
    setError("");

    const password = form.password;
    const confirmPassword = form.confirmPassword;
    const passwordTrimmed = password.trim();
    const confirmPasswordTrimmed = confirmPassword.trim();

    if (password !== confirmPassword) {
      if (passwordTrimmed === confirmPasswordTrimmed) {
        setError("Passwords look same but contain extra spaces. Remove spaces and try again.");
      } else {
        setError("Passwords do not match.");
      }
      setPending(false);
      return;
    }

    try {
      await registerUser({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        password: passwordTrimmed
      });

      navigate("/login", {
        replace: true,
        state: {
          registrationSuccess: "Registration successful. Please verify your email before signing in."
        }
      });
    } catch (requestError) {
      setError(requestError.message || "Unable to register.");
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
              <p className="eyebrow">Create account</p>
              <h1>Start with Click</h1>
              <p className="page-copy">Just a few details to open your workspace.</p>
            </div>
            <div className="auth-quick-points" aria-hidden="true">
              <span>Teams</span>
              <span>Files</span>
              <span>Tasks</span>
            </div>
          </div>

          <form className="form-shell auth-form-panel" onSubmit={handleSubmit}>
            {error ? <div className="error-banner">{error}</div> : null}

            <div className="auth-name-grid">
              <div className="field">
                <label htmlFor="first_name">First name</label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  className="text-input"
                  value={form.first_name}
                  onChange={handleChange}
                  placeholder="John"
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="last_name">Last name</label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  className="text-input"
                  value={form.last_name}
                  onChange={handleChange}
                  placeholder="Doe"
                  required
                />
              </div>
            </div>

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
                placeholder="Minimum 12 characters"
                minLength={12}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="confirmPassword">Confirm password</label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                className="text-input"
                value={form.confirmPassword}
                onChange={handleChange}
                placeholder="Re-enter password"
                minLength={12}
                required
              />
            </div>

            <div className="toolbar-actions auth-actions-grid">
              <button type="submit" className="btn btn-primary" disabled={pending}>
                {pending ? "Creating account..." : "Create account"}
              </button>
              <Link to="/login" className="btn btn-secondary">
                Back to sign in
              </Link>
            </div>

            <div className="auth-subactions">
              <Link to="/verify-email">Verify later</Link>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}
