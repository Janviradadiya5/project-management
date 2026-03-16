import { Link, NavLink, Outlet } from "react-router-dom";
import ClickWordmark from "./ClickWordmark.jsx";
import { useSession } from "../context/SessionContext.jsx";
import {
  canContribute,
  canManageOrganization,
  canManageProjects,
  canReadWorkspace,
  canViewActivityLogs,
  canViewMembers,
  getRoleLabel,
  getRoleTone
} from "../utils/roles.js";

const navigationGroups = [
  {
    label: "Command",
    items: [
      { to: "/", label: "Overview", caption: "Start here and see next actions", end: true, show: () => true },
      { to: "/organizations", label: "Organizations", caption: "Choose workspace context", show: () => true },
      { to: "/account", label: "Account", caption: "Profile and security settings", show: () => true }
    ]
  },
  {
    label: "Delivery",
    items: [
      { to: "/projects", label: "Projects", caption: "Plan scope and ownership", show: (role, isSuperAdmin) => canReadWorkspace(role, isSuperAdmin) },
      { to: "/tasks", label: "Tasks", caption: "Track progress and status", show: (role, isSuperAdmin) => canReadWorkspace(role, isSuperAdmin) },
      { to: "/notifications", label: "Inbox", caption: "Approvals and alerts", show: (role, isSuperAdmin) => canReadWorkspace(role, isSuperAdmin) }
    ]
  },
  {
    label: "Operations",
    items: [
      { to: "/comments", label: "Discussion", caption: "Comment and decisions", show: (role, isSuperAdmin) => canContribute(role, isSuperAdmin) },
      { to: "/attachments", label: "Files", caption: "Attach and manage docs", show: (role, isSuperAdmin) => canContribute(role, isSuperAdmin) },
      { to: "/people", label: "People", caption: "Members and roles", show: (role, isSuperAdmin) => canViewMembers(role, isSuperAdmin) },
      { to: "/activity", label: "Activity", caption: "Audit history", show: (role, isSuperAdmin) => canViewActivityLogs(role, isSuperAdmin) }
    ]
  }
];

export default function AppShell() {
  const { currentOrganization, isAuthenticated, isSuperAdmin, organizationId, organizationRole, logout, user } = useSession();
  const roleLabel = getRoleLabel(organizationRole, isSuperAdmin);
  const roleTone = getRoleTone(organizationRole, isSuperAdmin);
  const showExecutiveActions = canManageOrganization(organizationRole, isSuperAdmin) || canManageProjects(organizationRole, isSuperAdmin);

  return (
    <div className="app-frame">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <aside className="sidebar">
        <div className="brand-block brand-block-premium">
          <Link to="/" className="brand-link" aria-label="Open Click dashboard">
            <ClickWordmark className="click-wordmark-sidebar" />
          </Link>
          <p className="brand-copy">
            One workspace for planning, execution, and team updates.
          </p>
        </div>

        <section className="context-card">
          <div>
            <p className="section-label">Current context</p>
            <strong className="context-title">{currentOrganization?.name || "No organization selected"}</strong>
            <p className="context-copy">
              {organizationId ? "Workspace selected. Your pages and actions are now role-aware." : "Select an organization first to unlock project and task workflows."}
            </p>
          </div>
          <div className={`role-badge role-badge-${roleTone}`}>{roleLabel}</div>
        </section>

        <nav className="nav-groups" aria-label="Primary navigation">
          {navigationGroups.map((group) => {
            const visibleItems = group.items.filter((item) => item.show(organizationRole, isSuperAdmin));

            if (!visibleItems.length) {
              return null;
            }

            return (
              <section key={group.label} className="nav-group">
                <p className="nav-group-label">{group.label}</p>
                <div className="nav-group-list">
                  {visibleItems.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      end={item.end}
                      className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
                    >
                      <span className="nav-link-title">{item.label}</span>
                      <span className="nav-link-caption">{item.caption}</span>
                    </NavLink>
                  ))}
                </div>
              </section>
            );
          })}
        </nav>

        <div className="session-card">
          <p className="session-label">{isAuthenticated ? "Signed in" : "Guest mode"}</p>
          <strong>{user?.email || "Sign in to access your workspace"}</strong>
          <p className="session-meta">
            {showExecutiveActions ? "You can manage setup and delivery controls." : "Available actions adapt to your current role."}
          </p>
          <div className="session-actions">
            {isAuthenticated ? (
              <button type="button" className="btn btn-secondary" onClick={logout}>
                Sign out
              </button>
            ) : (
              <Link to="/login" className="btn btn-primary">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </aside>

      <main id="main-content" className="workspace" tabIndex="-1">
        <header className="workspace-header workspace-header-premium">
          <div>
            <p className="eyebrow">Execution Workspace</p>
            <h1>{currentOrganization?.name || "Portfolio Workspace"}</h1>
            <p>Project workspace.</p>
          </div>
          <div className="workspace-header-actions">
            <div className="workspace-badge">{organizationId ? "Workspace active" : "Select an organization"}</div>
            <div className={`role-badge role-badge-${roleTone}`}>{roleLabel}</div>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}