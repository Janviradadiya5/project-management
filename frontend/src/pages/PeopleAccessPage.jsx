import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  acceptOrganizationInvite,
  inviteOrganizationMember,
  listOrganizationInvites,
  listOrganizationMembers,
  removeOrganizationMember,
  revokeOrganizationInvite,
  updateOrganizationMember
} from "../api/client.js";
import EmptyState from "../components/EmptyState.jsx";
import LoadingGrid from "../components/LoadingGrid.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useNotifications } from "../context/NotificationContext.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatDate } from "../utils/format.js";
import { extractTokenFromValue } from "../utils/token.js";
import { canManageOrganization, canViewMembers } from "../utils/roles.js";
import { getMemberOptionLabel, getPersonLabel } from "../utils/display.js";

const roleCodeChoices = ["organization_admin", "project_manager", "team_member", "viewer"];

const initialInviteForm = {
  email: "",
  role_code: "team_member"
};

const initialMemberForm = {
  user_id: "",
  role_code: "team_member",
  status: "active"
};

export default function PeopleAccessPage() {
  const { accessToken, isAuthenticated, isSuperAdmin, organizationId, organizationRole, user } = useSession();
  const { pushToast } = useNotifications();
  const [members, setMembers] = useState([]);
  const [invites, setInvites] = useState([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [loadingInvites, setLoadingInvites] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");
  const [inviteForm, setInviteForm] = useState(initialInviteForm);
  const [acceptInviteLink, setAcceptInviteLink] = useState("");
  const [activeSection, setActiveSection] = useState("members");
  const [memberForm, setMemberForm] = useState(initialMemberForm);
  const [removeUserId, setRemoveUserId] = useState("");

  const canReadPeople = canViewMembers(organizationRole, isSuperAdmin);
  const canManagePeople = canManageOrganization(organizationRole, isSuperAdmin);

  const roleIdByCode = useMemo(() => {
    const map = new Map();

    for (const member of members) {
      if (member.role_code && member.role_id) {
        map.set(member.role_code, member.role_id);
      }
    }

    for (const invite of invites) {
      if (invite.role_code && invite.role_id) {
        map.set(invite.role_code, invite.role_id);
      }
    }

    return map;
  }, [invites, members]);

  const memberOptions = useMemo(
    () => members.map((member) => ({
      value: member.user_id,
      label: getMemberOptionLabel({
        id: member.user_id,
        name: member.user_name,
        email: member.user_email,
        roleName: member.role_name || member.role_code
      })
    })),
    [members]
  );

  function resolveRoleId(roleCode) {
    return roleIdByCode.get(roleCode) || "";
  }

  async function loadMembers() {
    if (!organizationId || !canReadPeople) {
      return;
    }

    setLoadingMembers(true);
    setError("");

    try {
      const response = await listOrganizationMembers(accessToken, organizationId, {
        limit: 100,
        page: 1,
        sort_by: "joined_at",
        order: "desc"
      });
      const loaded = response?.data?.items || [];
      setMembers(loaded);
      setMemberForm((current) => ({
        ...current,
        user_id: loaded.some((member) => member.user_id === current.user_id) ? current.user_id : loaded[0]?.user_id || "",
        role_code: current.role_code || loaded[0]?.role_code || "team_member"
      }));
      setRemoveUserId((current) => (loaded.some((member) => member.user_id === current) ? current : loaded[0]?.user_id || ""));
    } catch (requestError) {
      setError(requestError.message || "Unable to load organization members.");
    } finally {
      setLoadingMembers(false);
    }
  }

  async function loadInvites() {
    if (!organizationId || !canManagePeople) {
      return;
    }

    setLoadingInvites(true);
    setError("");

    try {
      const response = await listOrganizationInvites(accessToken, organizationId, {
        limit: 100,
        page: 1,
        sort_by: "created_at",
        order: "desc"
      });
      setInvites(response?.data?.items || []);
    } catch (requestError) {
      setError(requestError.message || "Unable to load invites.");
    } finally {
      setLoadingInvites(false);
    }
  }

  useEffect(() => {
    loadMembers();
    loadInvites();
  }, [accessToken, canManagePeople, canReadPeople, organizationId]);

  async function handleInviteSubmit(event) {
    event.preventDefault();

    if (!inviteForm.email.trim()) {
      setError("Invite email is required.");
      return;
    }

    const resolvedRoleId = resolveRoleId(inviteForm.role_code);

    setPending("invite");
    setError("");

    try {
      await inviteOrganizationMember(accessToken, organizationId, {
        email: inviteForm.email.trim(),
        ...(resolvedRoleId ? { role_id: resolvedRoleId } : { role_code: inviteForm.role_code })
      });
      setInviteForm(initialInviteForm);
      pushToast("Invitation sent.", "success");
      await loadInvites();
    } catch (requestError) {
      setError(requestError.message || "Unable to send invite.");
      pushToast("Invite failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleMemberUpdate(event) {
    event.preventDefault();

    if (!memberForm.user_id) {
      setError("Choose a member first.");
      return;
    }

    const resolvedRoleId = resolveRoleId(memberForm.role_code);

    setPending("member-update");
    setError("");

    try {
      await updateOrganizationMember(accessToken, organizationId, memberForm.user_id, {
        ...(resolvedRoleId ? { role_id: resolvedRoleId } : { role_code: memberForm.role_code }),
        status: memberForm.status
      });
      pushToast("Member access updated.", "success");
      await loadMembers();
    } catch (requestError) {
      setError(requestError.message || "Unable to update member.");
      pushToast("Member update failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleMemberRemove(event) {
    event.preventDefault();

    if (!removeUserId) {
      setError("Choose a member to remove.");
      return;
    }

    setPending("member-remove");
    setError("");

    try {
      await removeOrganizationMember(accessToken, organizationId, removeUserId);
      pushToast("Member removed from workspace.", "warning");
      setRemoveUserId("");
      await loadMembers();
    } catch (requestError) {
      setError(requestError.message || "Unable to remove member.");
      pushToast("Member removal failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleRevokeInvite(inviteId) {
    setPending(`invite-revoke:${inviteId}`);
    setError("");

    try {
      await revokeOrganizationInvite(accessToken, organizationId, inviteId);
      pushToast("Invite revoked.", "warning");
      await loadInvites();
    } catch (requestError) {
      setError(requestError.message || "Unable to revoke invite.");
      pushToast("Invite revoke failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleInlineMemberAction(userId, roleCode, status) {
    const roleId = resolveRoleId(roleCode);

    setPending(`member-inline:${userId}`);
    setError("");

    try {
      await updateOrganizationMember(accessToken, organizationId, userId, {
        ...(roleId ? { role_id: roleId } : { role_code: roleCode }),
        status
      });
      pushToast("Member access updated.", "success");
      await loadMembers();
    } catch (requestError) {
      setError(requestError.message || "Unable to update member.");
      pushToast("Member update failed.", "error");
    } finally {
      setPending("");
    }
  }

  async function handleAcceptInvite(event) {
    event.preventDefault();

    const parsedToken = extractTokenFromValue(acceptInviteLink);
    if (!parsedToken) {
      setError("Paste a valid workspace invite link.");
      return;
    }

    setPending("invite-accept");
    setError("");

    try {
      await acceptOrganizationInvite(accessToken, { token: parsedToken });
      setAcceptInviteLink("");
      pushToast("Invite accepted.", "success");
      await loadMembers();
      await loadInvites();
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
          title="Sign in to open people access"
          description="Manage organization members and invitation flow from one control surface."
          action={
            <Link to="/login" className="btn btn-primary">
              Open sign in
            </Link>
          }
        />
      </section>
    );
  }

  if (!organizationId) {
    return (
      <section className="page">
        <EmptyState
          title="Select a workspace first"
          description="Choose an organization before opening member and invitation controls."
          action={
            <Link to="/organizations" className="btn btn-primary">
              Choose workspace
            </Link>
          }
        />
      </section>
    );
  }

  if (!canReadPeople) {
    return (
      <section className="page">
        <EmptyState
          title="Member access is restricted"
          description="Only managers and admins can open member visibility and invitation controls in this workspace."
          action={
            <Link to="/" className="btn btn-primary">
              Back to overview
            </Link>
          }
        />
      </section>
    );
  }

  return (
    <section className="page">
      <PageHeader
        eyebrow="People"
        title="People and access"
        description="Members and access controls."
      />

      <section className="panel tasks-intro-panel">
        <div className="tasks-intro-copy">
          <p className="section-label">Workspace mode</p>
          <h3 className="section-heading">People controls</h3>
          <p className="helper-text">Open one section and continue.</p>
          <div className="tasks-view-switch" role="tablist" aria-label="People sections">
            <button
              type="button"
              className={`tasks-view-button${activeSection === "members" ? " active" : ""}`}
              onClick={() => setActiveSection("members")}
            >
              Members
            </button>
            <button
              type="button"
              className={`tasks-view-button${activeSection === "access" ? " active" : ""}`}
              onClick={() => setActiveSection("access")}
            >
              Access
            </button>
            <button
              type="button"
              className={`tasks-view-button${activeSection === "invites" ? " active" : ""}`}
              onClick={() => setActiveSection("invites")}
            >
              Invites
            </button>
          </div>
        </div>
        <div className="tasks-intro-metrics">
          <div>
            <p className="data-meta">Members</p>
            <strong>{members.length}</strong>
          </div>
          <div>
            <p className="data-meta">Invites</p>
            <strong>{invites.length}</strong>
          </div>
          <div>
            <p className="data-meta">Mode</p>
            <strong>{canManagePeople ? "Manager" : "Viewer"}</strong>
          </div>
          <div>
            <p className="data-meta">Focus</p>
            <strong>{activeSection}</strong>
          </div>
        </div>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      {activeSection === "members" ? (
      <section className="panel">
        <h3 className="section-heading">Active members</h3>
        {loadingMembers ? <LoadingGrid cards={2} /> : null}
        {!loadingMembers && !members.length ? <p className="muted">No active members found.</p> : null}
        <div className="data-list">
          {members.map((member) => (
            <article key={member.id} className="data-card">
              <div className="data-card-header">
                <div>
                  <h3>
                    {getPersonLabel({
                      id: member.user_id,
                      name: member.user_name,
                      email: member.user_email,
                      currentUserId: user?.id
                    })}
                  </h3>
                  <p>{member.user_email || "No email available"}</p>
                </div>
                <StatusPill value={member.status || "active"} />
              </div>
              <div className="list-row">
                <div>
                  <p className="data-meta">Access</p>
                  <strong>{member.role_name || member.role_code}</strong>
                </div>
                <div>
                  <p className="data-meta">Joined</p>
                  <strong>{formatDate(member.joined_at)}</strong>
                </div>
                <div>
                  <p className="data-meta">Invited by</p>
                  <strong>{member.invited_by_user_name || "System"}</strong>
                </div>
              </div>
              {canManagePeople ? (
                <div className="toolbar-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    disabled={pending === `member-inline:${member.user_id}` || member.status === "active"}
                    onClick={() => handleInlineMemberAction(member.user_id, member.role_code, "active")}
                  >
                    Activate
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    disabled={pending === `member-inline:${member.user_id}` || member.status === "suspended"}
                    onClick={() => handleInlineMemberAction(member.user_id, member.role_code, "suspended")}
                  >
                    Suspend
                  </button>
                  {member.role_code !== "project_manager" ? (
                    <button
                      type="button"
                      className="btn btn-secondary"
                      disabled={pending === `member-inline:${member.user_id}`}
                      onClick={() => handleInlineMemberAction(member.user_id, "project_manager", member.status || "active")}
                    >
                      Make manager
                    </button>
                  ) : null}
                  {member.role_code !== "team_member" ? (
                    <button
                      type="button"
                      className="btn btn-secondary"
                      disabled={pending === `member-inline:${member.user_id}`}
                      onClick={() => handleInlineMemberAction(member.user_id, "team_member", member.status || "active")}
                    >
                      Make member
                    </button>
                  ) : null}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      </section>
      ) : null}

      {activeSection === "access" ? (!canManagePeople ? (
        <section className="panel"><p className="muted">Manager or admin role required to manage access.</p></section>
      ) : (
        <section className="split-grid people-access-grid">
          <form className="panel form-shell invite-form" onSubmit={handleInviteSubmit}>
            <h3 className="section-heading">Send invite</h3>
            <div className="field">
              <label htmlFor="invite-email">Member email</label>
              <input
                id="invite-email"
                className="text-input"
                value={inviteForm.email}
                onChange={(event) => setInviteForm((current) => ({ ...current, email: event.target.value }))}
                placeholder="name@company.com"
                required
              />
            </div>
            <div className="field">
              <label htmlFor="invite-role-code">Role</label>
              <select
                id="invite-role-code"
                className="select-input"
                value={inviteForm.role_code}
                onChange={(event) => setInviteForm((current) => ({ ...current, role_code: event.target.value }))}
              >
                {roleCodeChoices.map((roleCode) => (
                  <option key={roleCode} value={roleCode}>
                    {roleCode.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" className="btn btn-primary invite-submit-btn" disabled={pending === "invite"}>
              {pending === "invite" ? "Sending..." : "Send invite"}
            </button>
          </form>

          <div className="panel form-shell">
            <form className="form-shell" onSubmit={handleMemberUpdate}>
              <h3 className="section-heading">Adjust member access</h3>
              <div className="field">
                <label htmlFor="member-user-select">Member</label>
                <select
                  id="member-user-select"
                  className="select-input"
                  value={memberForm.user_id}
                  onChange={(event) => {
                    const selectedMember = members.find((member) => member.user_id === event.target.value);
                    setMemberForm((current) => ({
                      ...current,
                      user_id: event.target.value,
                      role_code: selectedMember?.role_code || current.role_code,
                      status: selectedMember?.status || current.status
                    }));
                  }}
                  required
                >
                  <option value="">Choose member</option>
                  {memberOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="member-role-code">Role</label>
                <select
                  id="member-role-code"
                  className="select-input"
                  value={memberForm.role_code}
                  onChange={(event) => setMemberForm((current) => ({ ...current, role_code: event.target.value }))}
                >
                  {roleCodeChoices.map((roleCode) => (
                    <option key={roleCode} value={roleCode}>
                      {roleCode.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="member-status">Status</label>
                <select
                  id="member-status"
                  className="select-input"
                  value={memberForm.status}
                  onChange={(event) => setMemberForm((current) => ({ ...current, status: event.target.value }))}
                >
                  <option value="active">active</option>
                  <option value="suspended">suspended</option>
                </select>
              </div>
              <button type="submit" className="btn btn-secondary" disabled={pending === "member-update"}>
                {pending === "member-update" ? "Updating..." : "Save access changes"}
              </button>
            </form>

            <form className="form-shell" onSubmit={handleMemberRemove}>
              <h3 className="section-heading">Remove member</h3>
              <div className="field">
                <label htmlFor="remove-user-select">Member</label>
                <select
                  id="remove-user-select"
                  className="select-input"
                  value={removeUserId}
                  onChange={(event) => setRemoveUserId(event.target.value)}
                  required
                >
                  <option value="">Choose member</option>
                  {memberOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <button type="submit" className="btn btn-secondary" disabled={pending === "member-remove"}>
                {pending === "member-remove" ? "Removing..." : "Remove from workspace"}
              </button>
            </form>

            <form className="form-shell" onSubmit={handleAcceptInvite}>
              <h3 className="section-heading">Accept workspace invite</h3>
              <div className="field">
                <label htmlFor="people-accept-invite-link">Invite link</label>
                <input
                  id="people-accept-invite-link"
                  className="text-input"
                  value={acceptInviteLink}
                  onChange={(event) => setAcceptInviteLink(event.target.value)}
                  placeholder="Paste workspace invite link"
                  required
                />
              </div>
              <button type="submit" className="btn btn-secondary" disabled={pending === "invite-accept"}>
                {pending === "invite-accept" ? "Joining..." : "Accept invite"}
              </button>
            </form>
          </div>
        </section>
      )) : null}

      {activeSection === "invites" ? (!canManagePeople ? (
        <section className="panel"><p className="muted">Manager or admin role required to view invites.</p></section>
      ) : (
        <section className="panel">
          <div className="data-card-header">
            <div>
              <h3>Open invites</h3>
              <p>Pending invitations stay visible here until accepted or revoked.</p>
            </div>
          </div>
          {loadingInvites ? <LoadingGrid cards={2} /> : null}
          {!loadingInvites && !invites.length ? <p className="muted">No open invites found.</p> : null}
          <div className="data-list">
            {invites.map((invite) => (
              <article key={invite.id} className="data-card">
                <div className="data-card-header">
                  <div>
                    <h3>{invite.email}</h3>
                    <p>{invite.role_name || invite.role_code}</p>
                  </div>
                  <StatusPill value={invite.revoked_at ? "revoked" : invite.accepted_at ? "accepted" : "pending"} />
                </div>
                <div className="list-row">
                  <div>
                    <p className="data-meta">Invited by</p>
                    <strong>{invite.invited_by_user_name || "System"}</strong>
                  </div>
                  <div>
                    <p className="data-meta">Expires</p>
                    <strong>{formatDate(invite.expires_at)}</strong>
                  </div>
                  <div>
                    <p className="data-meta">Accepted</p>
                    <strong>{formatDate(invite.accepted_at)}</strong>
                  </div>
                </div>
                <div className="toolbar-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    disabled={Boolean(invite.revoked_at || invite.accepted_at) || pending === `invite-revoke:${invite.id}`}
                    onClick={() => handleRevokeInvite(invite.id)}
                  >
                    {pending === `invite-revoke:${invite.id}` ? "Revoking..." : "Revoke invite"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )) : null}
    </section>
  );
}
