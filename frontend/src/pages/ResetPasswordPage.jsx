import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { confirmPasswordReset } from "../api/client.js";
import ClickWordmark from "../components/ClickWordmark.jsx";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    setToken(searchParams.get("token") || "");
  }, [searchParams]);

  async function handleSubmit(event) {
    event.preventDefault();
    setPending(true);
    setError("");
    setSuccess("");

    if (password !== confirmPassword) {
      setPending(false);
      setError("Passwords do not match.");
      return;
    }

    try {
      await confirmPasswordReset({ token: token.trim(), new_password: password });
      setSuccess("Password reset successful. Sign in with your new password.");
      setPassword("");
      setConfirmPassword("");
    } catch (requestError) {
      setError(requestError.message || "Unable to reset password.");
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
          <p className="eyebrow">Reset Password</p>
          <h1>Choose a new password</h1>
          <p className="page-copy">Use the reset token from your email and set a strong new password.</p>
        </div>

        {error ? <div className="error-banner">{error}</div> : null}
        {success ? <div className="success-banner">{success}</div> : null}

        <form className="form-shell" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="reset-token">Reset token</label>
            <input id="reset-token" className="text-input" value={token} onChange={(event) => setToken(event.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="reset-password">New password</label>
            <input id="reset-password" type="password" className="text-input" value={password} onChange={(event) => setPassword(event.target.value)} minLength={12} required />
          </div>
          <div className="field">
            <label htmlFor="reset-password-confirm">Confirm password</label>
            <input id="reset-password-confirm" type="password" className="text-input" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} minLength={12} required />
          </div>
          <div className="toolbar-actions">
            <button type="submit" className="btn btn-primary" disabled={pending}>
              {pending ? "Saving..." : "Reset password"}
            </button>
            <Link to="/login" className="btn btn-secondary">Back to sign in</Link>
          </div>
        </form>
      </section>
    </div>
  );
}