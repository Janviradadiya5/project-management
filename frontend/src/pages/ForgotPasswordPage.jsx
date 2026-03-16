import { useState } from "react";
import { Link } from "react-router-dom";
import { requestPasswordReset } from "../api/client.js";
import ClickWordmark from "../components/ClickWordmark.jsx";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setPending(true);
    setError("");
    setSuccess("");

    try {
      await requestPasswordReset({ email: email.trim() });
      setSuccess("Password reset instructions sent.");
    } catch (requestError) {
      setError(requestError.message || "Unable to send reset instructions.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="login-card form-shell">
        <div className="auth-brand">
          <ClickWordmark className="click-wordmark-auth" />
        </div>
        <div>
          <p className="eyebrow">Password Reset</p>
          <h1>Get a fresh password link</h1>
          <p className="page-copy">Enter your email and we will send reset instructions.</p>
        </div>

        {error ? <div className="error-banner">{error}</div> : null}
        {success ? <div className="success-banner">{success}</div> : null}

        <form className="form-shell" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="forgot-password-email">Email</label>
            <input id="forgot-password-email" type="email" className="text-input" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required />
          </div>
          <div className="toolbar-actions">
            <button type="submit" className="btn btn-primary" disabled={pending}>
              {pending ? "Sending..." : "Send reset link"}
            </button>
            <Link to="/login" className="btn btn-secondary">Back to sign in</Link>
          </div>
        </form>
      </section>
    </div>
  );
}