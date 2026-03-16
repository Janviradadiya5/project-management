import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { acceptOrganizationInvite, getProfile, requestEmailVerification, updateProfile } from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import PageHeader from "../components/PageHeader.jsx";
import { useNotifications } from "../context/NotificationContext.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { extractTokenFromValue } from "../utils/token.js";

export default function AccountSettingsPage() {
  const { accessToken, isAuthenticated, setUser, user } = useSession();
  const { pushToast } = useNotifications();
  const [profileForm, setProfileForm] = useState({ first_name: "", last_name: "" });
  const [verificationEmail, setVerificationEmail] = useState("");
  const [inviteLink, setInviteLink] = useState("");
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    setProfileForm({
      first_name: user?.first_name || "",
      last_name: user?.last_name || ""
    });
    setVerificationEmail(user?.email || "");
  }, [user?.email, user?.first_name, user?.last_name]);

  async function refreshProfile() {
    const response = await getProfile(accessToken);
    setUser(response?.data || null);
  }

  async function handleProfileSave(event) {
    event.preventDefault();
    setPending("profile");
    setError("");
    setSuccess("");

    try {
      const response = await updateProfile(accessToken, profileForm);
      setUser(response?.data || null);
      setSuccess("Profile updated.");
      pushToast("Profile updated.", "success");
    } catch (requestError) {
      setError(requestError.message || "Unable to update profile.");
      pushToast("Profile update failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleVerificationRequest(event) {
    event.preventDefault();
    setPending("verification");
    setError("");
    setSuccess("");

    try {
      await requestEmailVerification({ email: verificationEmail });
      setSuccess("Verification email sent.");
      pushToast("Verification email sent.", "success");
    } catch (requestError) {
      setError(requestError.message || "Unable to send verification email.");
      pushToast("Verification request failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleInviteAccept(event) {
    event.preventDefault();
    setPending("invite");
    setError("");
    setSuccess("");

    const parsedToken = extractTokenFromValue(inviteLink);
    if (!parsedToken) {
      setPending("");
      setError("Paste a valid workspace invite link.");
      return;
    }

    try {
      await acceptOrganizationInvite(accessToken, { token: parsedToken });
      setInviteLink("");
      setSuccess("Invite accepted. Your new workspace is ready.");
      pushToast("Invite accepted.", "success");
      await refreshProfile();
    } catch (requestError) {
      setError(requestError.message || "Unable to accept invite.");
      pushToast("Invite accept failed.", "error");
    } finally {
      setPending("");
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="page">
        <EmptyState
          title="Sign in to open account settings"
          description="Profile updates and invite acceptance are available after sign in."
          action={
            <Link to="/login" className="btn btn-primary">
              Open sign in
            </Link>
          }
        />
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="Account"
        title="Account settings"
        description="Update your profile, resend verification, and join invited workspaces from one place."
      />

      {error ? <div className="error-banner">{error}</div> : null}
      {success ? <div className="success-banner">{success}</div> : null}

      <section className="split-grid">
        <form className="panel form-shell" onSubmit={handleProfileSave}>
          <h3 className="section-heading">Profile</h3>
          <div className="field">
            <label htmlFor="account-first-name">First name</label>
            <input id="account-first-name" className="text-input" value={profileForm.first_name} onChange={(event) => setProfileForm((current) => ({ ...current, first_name: event.target.value }))} required />
          </div>
          <div className="field">
            <label htmlFor="account-last-name">Last name</label>
            <input id="account-last-name" className="text-input" value={profileForm.last_name} onChange={(event) => setProfileForm((current) => ({ ...current, last_name: event.target.value }))} required />
          </div>
          <div className="field">
            <label htmlFor="account-email">Email</label>
            <input id="account-email" className="text-input" value={user?.email || ""} disabled />
          </div>
          <button type="submit" className="btn btn-primary" disabled={pending === "profile"}>
            {pending === "profile" ? "Saving..." : "Save profile"}
          </button>
        </form>

        <div className="panel form-shell">
          <form className="form-shell" onSubmit={handleVerificationRequest}>
            <h3 className="section-heading">Email verification</h3>
            <div className="field">
              <label htmlFor="verification-email">Email</label>
              <input id="verification-email" className="text-input" value={verificationEmail} onChange={(event) => setVerificationEmail(event.target.value)} required />
            </div>
            <button type="submit" className="btn btn-secondary" disabled={pending === "verification"}>
              {pending === "verification" ? "Sending..." : user?.is_email_verified ? "Send another verification link" : "Send verification link"}
            </button>
          </form>

          <form className="form-shell" onSubmit={handleInviteAccept}>
            <h3 className="section-heading">Accept workspace invite</h3>
            <div className="field">
              <label htmlFor="invite-link">Invite link</label>
              <input
                id="invite-link"
                className="text-input"
                value={inviteLink}
                onChange={(event) => setInviteLink(event.target.value)}
                placeholder="Paste workspace invite link"
                required
              />
            </div>
            <button type="submit" className="btn btn-secondary" disabled={pending === "invite"}>
              {pending === "invite" ? "Joining..." : "Accept invite"}
            </button>
          </form>
        </div>
      </section>
    </section>
  );
}