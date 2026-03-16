import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { confirmEmailVerification, requestEmailVerification } from "../api/client.js";
import ClickWordmark from "../components/ClickWordmark.jsx";
import { extractTokenFromValue } from "../utils/token.js";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const [verificationLink, setVerificationLink] = useState("");
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [autoToken, setAutoToken] = useState("");
  const [autoVerified, setAutoVerified] = useState(false);

  useEffect(() => {
    const tokenFromQuery = searchParams.get("token") || "";
    setAutoToken(tokenFromQuery);
  }, [searchParams]);

  useEffect(() => {
    async function runAutoVerify() {
      if (!autoToken || autoVerified) {
        return;
      }

      setPending("confirm");
      setError("");
      setSuccess("");

      try {
        await confirmEmailVerification({ token: autoToken.trim() });
        setSuccess("Email verified successfully. You can sign in now.");
        setAutoVerified(true);
      } catch (requestError) {
        setError(requestError.message || "Unable to verify email.");
      } finally {
        setPending("");
      }
    }

    runAutoVerify();
  }, [autoToken, autoVerified]);

  async function handleConfirm(event) {
    event.preventDefault();
    setPending("confirm");
    setError("");
    setSuccess("");

    const parsedToken = extractTokenFromValue(verificationLink);
    if (!parsedToken) {
      setPending("");
      setError("Paste a valid verification link.");
      return;
    }

    try {
      await confirmEmailVerification({ token: parsedToken });
      setSuccess("Email verified successfully. You can sign in now.");
    } catch (requestError) {
      setError(requestError.message || "Unable to verify email.");
    } finally {
      setPending("");
    }
  }

  async function handleRequest(event) {
    event.preventDefault();
    setPending("request");
    setError("");
    setSuccess("");

    try {
      await requestEmailVerification({ email: email.trim() });
      setSuccess("Verification link sent.");
    } catch (requestError) {
      setError(requestError.message || "Unable to send verification link.");
    } finally {
      setPending("");
    }
  }

  return (
    <div className="login-shell">
      <section className="login-card form-shell">
        <div className="auth-brand">
          <ClickWordmark className="click-wordmark-auth" />
        </div>
        <div>
          <p className="eyebrow">Verify Email</p>
          <h1>Confirm your email address</h1>
          <p className="page-copy">Open the verification link from your email. You can also paste the full link below.</p>
        </div>

        {error ? <div className="error-banner">{error}</div> : null}
        {success ? <div className="success-banner">{success}</div> : null}

        <form className="form-shell" onSubmit={handleConfirm}>
          <div className="field">
            <label htmlFor="verify-link">Verification link</label>
            <input
              id="verify-link"
              className="text-input"
              value={verificationLink}
              onChange={(event) => setVerificationLink(event.target.value)}
              placeholder="Paste full verification link"
              required={!autoToken}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={pending === "confirm" || !verificationLink.trim()}>
            {pending === "confirm" ? "Verifying..." : "Verify using link"}
          </button>
        </form>

        <form className="form-shell" onSubmit={handleRequest}>
          <div className="field">
            <label htmlFor="verify-email-request">Email</label>
            <input id="verify-email-request" type="email" className="text-input" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required />
          </div>
          <div className="toolbar-actions">
            <button type="submit" className="btn btn-secondary" disabled={pending === "request"}>
              {pending === "request" ? "Sending..." : "Send new link"}
            </button>
            <Link to="/login" className="btn btn-secondary">Back to sign in</Link>
          </div>
        </form>
      </section>
    </div>
  );
}