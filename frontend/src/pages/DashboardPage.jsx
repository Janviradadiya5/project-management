import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { getProfile, pingApiHealth } from "../api/client.js";
import ClickWordmark from "../components/ClickWordmark.jsx";
import MetricCard from "../components/MetricCard.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusPill from "../components/StatusPill.jsx";
import { useSession } from "../context/SessionContext.jsx";
import { formatId } from "../utils/format.js";
import { canContribute, canManageOrganization, canManageProjects, getRoleLabel } from "../utils/roles.js";

export default function DashboardPage() {
  const { accessToken, currentOrganization, isAuthenticated, isSuperAdmin, organizationId, organizationRole, user, setUser } = useSession();
  const [health, setHealth] = useState({ state: "checking", text: "Syncing workspace status..." });
  const [guidanceIndex, setGuidanceIndex] = useState(0);
  const [activeSection, setActiveSection] = useState("overview");
  const isPreviewMode = !isAuthenticated;
  const isExecutive = canManageOrganization(organizationRole, isSuperAdmin);
  const canDriveProjects = canManageProjects(organizationRole, isSuperAdmin);
  const canExecute = canContribute(organizationRole, isSuperAdmin);

  useEffect(() => {
    let active = true;

    async function run() {
      const result = await pingApiHealth();
      if (!active) {
        return;
      }

      if (result.ok) {
        setHealth({ state: "online", text: "Workspace services are running smoothly." });
      } else {
        setHealth({ state: "offline", text: "Workspace services are temporarily unavailable." });
      }
    }

    run();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function hydrateProfile() {
      if (!isAuthenticated || user?.created_at) {
        return;
      }

      try {
        const profile = await getProfile(accessToken);
        if (active) {
          setUser(profile?.data || null);
        }
      } catch {
        // Keep the login payload if the profile call fails.
      }
    }

    hydrateProfile();
    return () => {
      active = false;
    };
  }, [accessToken, isAuthenticated, setUser, user]);

  const roleLabel = getRoleLabel(organizationRole, isSuperAdmin);
  const metrics = [
    { label: "System health", value: health.state === "online" ? "Operational" : "Needs review", trend: health.text },
    { label: "Access profile", value: roleLabel, trend: user?.email || "Sign in to unlock your workspace" },
    { label: "Active organization", value: currentOrganization?.name || "Not selected", trend: organizationId ? formatId(organizationId) : "Choose a workspace to continue" },
    { label: "Delivery posture", value: canDriveProjects ? "Control" : canExecute ? "Execution" : "Visibility", trend: isExecutive ? "Administrative authority enabled" : "Actions adapt to your role" }
  ];

  const guidanceCards = [
    {
      eyebrow: "Step 1: Workspace",
      title: "Select your active workspace.",
      points: [
        "Choose the right org so every project and task stays aligned."
      ],
      to: "/organizations",
      ctaLabel: "Open organizations"
    },
    {
      eyebrow: "Step 2: Project Setup",
      title: "Set project scope and owner.",
      points: [
        "Keep outcome, due plan, and owner visible from day one."
      ],
      to: "/projects",
      ctaLabel: "Open projects"
    },
    {
      eyebrow: "Step 3: Task Flow",
      title: "Run delivery through tasks.",
      points: [
        canDriveProjects
          ? "Create, assign, and prioritize in one execution board."
          : "Track owners, priority, and deadlines in one place.",
        canExecute ? "Post status and blockers quickly." : "Review progress and keep alignment."
      ],
      to: "/tasks",
      ctaLabel: "Open task board"
    },
    {
      eyebrow: "Step 4: Team Communication",
      title: "Keep discussion near work.",
      points: [
        "Capture decisions and updates directly on tasks."
      ],
      to: "/comments",
      ctaLabel: "Open comments"
    },
    {
      eyebrow: "Step 5: Files & Proof",
      title: "Attach files in task flow.",
      points: [
        "Keep specs, assets, and approvals in one traceable place."
      ],
      to: "/attachments",
      ctaLabel: "Open attachments"
    },
    {
      eyebrow: "Step 6: Daily Review",
      title: "Review daily alerts first.",
      points: [
        "Check blockers and owner updates before starting execution."
      ],
      to: "/notifications",
      ctaLabel: "Open notifications"
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setGuidanceIndex((prev) => (prev + 1) % guidanceCards.length);
    }, 4200);

    return () => {
      clearInterval(timer);
    };
  }, [guidanceCards.length]);

  return (
    <section className={`page page-clear${isPreviewMode ? " page-preview" : ""}`}>
      {isPreviewMode ? (
        <section className="landing-hero-shell panel">
          <div className="landing-topbar">
            <div className="landing-brand">
              <ClickWordmark className="click-wordmark-preview-header" />
            </div>
            <nav className="landing-nav" aria-label="Marketing navigation">
              <NavLink to="/product" className="landing-nav-link">Product</NavLink>
              <NavLink to="/solutions" className="landing-nav-link">Solutions</NavLink>
              <NavLink to="/learn" className="landing-nav-link">Learn</NavLink>
              <NavLink to="/pricing" className="landing-nav-link">Pricing</NavLink>
              <NavLink to="/enterprise" className="landing-nav-link">Enterprise</NavLink>
            </nav>
            <div className="landing-auth-actions">
              <Link to="/register" className="btn btn-secondary">Sign up</Link>
              <Link to="/login" className="btn btn-primary">Log in</Link>
            </div>
          </div>

          <div className="landing-hero-grid">
            <div className="landing-copy">
              <p className="eyebrow">Project + task + discussion</p>
              <h1>
                <span className="landing-title-gradient">One app to replace team chaos.</span>
              </h1>
              <p className="hero-subtitle">
                Plan projects, run tasks, and keep updates visible from one clean workspace that first-time users understand instantly.
              </p>
              <div className="landing-cta-row">
                <Link to="/register" className="btn btn-primary">Get started</Link>
                <Link to="/login" className="btn btn-secondary">Open live preview</Link>
              </div>
              <p className="landing-proof">Invite your team, align projects, and move every task from plan to done.</p>
              <div className="landing-kpi-row" aria-label="Workspace impact">
                <div className="landing-kpi-item">
                  <strong>3x</strong>
                  <span>faster planning</span>
                </div>
                <div className="landing-kpi-item">
                  <strong>24/7</strong>
                  <span>status visibility</span>
                </div>
                <div className="landing-kpi-item">
                  <strong>1 place</strong>
                  <span>tasks, chat, docs</span>
                </div>
              </div>
            </div>

            <div className="landing-visual">
              <div className="landing-mock-main">
                <div className="landing-mock-row">
                  <span className="clear-badge mint">Ready</span>
                  <span>Finalize campaign brief</span>
                </div>
                <div className="landing-mock-row">
                  <span className="clear-badge blue">In progress</span>
                  <span>Write launch copy</span>
                </div>
                <div className="landing-mock-row">
                  <span className="clear-badge amber">Review</span>
                  <span>Stakeholder sign-off</span>
                </div>
              </div>
              <div className="landing-mock-note">
                <p>Chat</p>
                <strong>Need final QA by 5 PM.</strong>
              </div>
              <div className="landing-mock-doc">
                <p>Docs</p>
                <strong>Meeting notes synced with task updates.</strong>
              </div>
              <div className="landing-mock-sync">
                <p>Timeline</p>
                <strong>3 tasks auto-assigned for this sprint.</strong>
              </div>
              <div className="landing-mock-alert">
                <p>Alert</p>
                <strong>2 blockers flagged for quick review.</strong>
              </div>
            </div>
          </div>
        </section>
      ) : (
        <PageHeader
          eyebrow="Workspace home"
          title={currentOrganization?.name ? `${currentOrganization.name} workspace` : "Start your work in 3 simple steps"}
          description="Keep planning, delivery, and updates in one command view."
          actions={
            <>
              <Link to="/organizations" className="btn btn-primary">
                Open workspace
              </Link>
              <Link to={canDriveProjects ? "/projects" : "/tasks"} className="btn btn-secondary">
                {canDriveProjects ? "Open projects" : "Open tasks"}
              </Link>
            </>
          }
        />
      )}

      <section className="panel tasks-intro-panel">
        <div className="tasks-intro-copy">
          <p className="section-label">Overview mode</p>
          <h3 className="section-heading">Choose one focus section</h3>
          <p className="helper-text">Compact view with only key controls.</p>
          <div className="tasks-view-switch" role="tablist" aria-label="Overview sections">
            <button type="button" className={`tasks-view-button${activeSection === "overview" ? " active" : ""}`} onClick={() => setActiveSection("overview")}>Overview</button>
            <button type="button" className={`tasks-view-button${activeSection === "guidance" ? " active" : ""}`} onClick={() => setActiveSection("guidance")}>Guidance</button>
            <button type="button" className={`tasks-view-button${activeSection === "command" ? " active" : ""}`} onClick={() => setActiveSection("command")}>Command</button>
          </div>
        </div>
        <div className="tasks-intro-metrics">
          <div>
            <p className="data-meta">Service</p>
            <strong>{health.state === "online" ? "Online" : "Review"}</strong>
          </div>
          <div>
            <p className="data-meta">Role</p>
            <strong>{roleLabel}</strong>
          </div>
          <div>
            <p className="data-meta">Workspace</p>
            <strong>{currentOrganization?.name || "None"}</strong>
          </div>
          <div>
            <p className="data-meta">Focus</p>
            <strong>{activeSection}</strong>
          </div>
        </div>
      </section>

      {activeSection === "overview" ? (
      <section className="dashboard-section partition-foundation">
        <div className="section-partition-head">
          <p className="section-partition-kicker">Foundation</p>
          <h3>Core flow</h3>
        </div>
        <section className="clear-hero panel">
          <div className="clear-hero-copy">
            <p className="section-label">Start here</p>
            <h3 className="section-heading">Move from setup to delivery fast</h3>
            <p className="helper-text">
              Select workspace, set scope, and execute from one stream.
            </p>
            <div className="clear-flow-grid" role="list" aria-label="Foundation workflow summary">
              <article className="clear-flow-card" role="listitem">
                <strong>01. Select workspace</strong>
                <p>Pick active org first.</p>
              </article>
              <article className="clear-flow-card" role="listitem">
                <strong>02. Set project direction</strong>
                <p>Define owner and priority.</p>
              </article>
              <article className="clear-flow-card" role="listitem">
                <strong>03. Track execution</strong>
                <p>Keep status, comments, and files together.</p>
              </article>
            </div>
            <div className="clear-hero-actions">
              <Link to="/organizations" className="btn btn-primary">1. Select organization</Link>
              <Link to={canDriveProjects ? "/projects" : "/tasks"} className="btn btn-secondary">2. Continue workflow</Link>
            </div>
          </div>
          <div className="clear-hero-status">
            <div className="clear-status-head">
              <p>Live context</p>
              <StatusPill value={health.state} />
            </div>
            <div className="clear-status-grid">
              <div className="clear-status-item">
                <span>Role</span>
                <strong>{roleLabel}</strong>
              </div>
              <div className="clear-status-item">
                <span>Workspace</span>
                <strong>{currentOrganization?.name || "Not selected"}</strong>
              </div>
              <div className="clear-status-item">
                <span>Service</span>
                <strong>{health.state === "online" ? "Ready" : "Check status"}</strong>
              </div>
            </div>
            <div className="clear-status-actions">
              <p>Next best actions</p>
              <Link to="/organizations" className="clear-inline-link">Set workspace context</Link>
              <Link to={canDriveProjects ? "/projects" : "/tasks"} className="clear-inline-link">
                {canDriveProjects ? "Define project scope" : "Open execution board"}
              </Link>
              <Link to="/notifications" className="clear-inline-link">Review latest updates</Link>
            </div>
          </div>
        </section>
      </section>
      ) : null}

      {activeSection === "guidance" ? (
      <section className="dashboard-section partition-guidance">
        <div className="section-partition-head guidance-partition-head">
          <p className="section-partition-kicker">GUIDANCE</p>
          <h3>Step by step actions</h3>
        </div>
        <section className="guidance-slider-shell panel" aria-label="Guidance slides">
          <div className="guidance-slider-window">
            <div className="guidance-slider-track" style={{ transform: `translateX(-${guidanceIndex * 100}%)` }}>
              {guidanceCards.map((card, index) => (
                <article key={card.title} className="guidance-slide-card">
                  <p className="guidance-slide-kicker">{card.eyebrow}</p>
                  <h4>{card.title}</h4>
                  <ul className="guidance-slide-points">
                    {card.points.map((point) => (
                      <li key={point}>{point}</li>
                    ))}
                  </ul>
                  <div className="guidance-slide-foot">
                    <Link to={card.to} className="guidance-slide-link">{card.ctaLabel}</Link>
                    <span className="guidance-slide-badge">Slide {index + 1}/{guidanceCards.length}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
          <div className="guidance-slider-controls" role="tablist" aria-label="Guidance slide controls">
            {guidanceCards.map((card, index) => (
              <button
                key={card.title}
                type="button"
                className={`guidance-dot${guidanceIndex === index ? " active" : ""}`}
                onClick={() => setGuidanceIndex(index)}
                aria-label={`Show guidance slide ${index + 1}`}
                aria-selected={guidanceIndex === index}
                role="tab"
              />
            ))}
          </div>
        </section>
      </section>
      ) : null}

      {activeSection === "command" ? (
      <section className="dashboard-section partition-insights partition-command-dark">
        <div className="section-partition-head">
          <p className="section-partition-kicker">Command</p>
          <h3>Delivery operation</h3>
        </div>
        <section className="insights-pro-shell panel command-dark-shell">
          <article className="insights-overview-card command-dark-card">
            <p className="section-label">Now</p>
            <h4>Track command, delivery, and risk from one panel.</h4>
            <div className="insights-health-strip">
              <span className="insights-pill">Health: {health.state === "online" ? "Stable" : "Review"}</span>
              <span className="insights-pill">Mode: {canDriveProjects ? "Control" : "Execution"}</span>
              <span className="insights-pill">Org: {currentOrganization?.name || "None"}</span>
            </div>
            <div className="preview-command-actions">
              <Link to="/tasks" className="clear-inline-link">Open tasks</Link>
              <Link to="/projects" className="clear-inline-link">Open projects</Link>
              <Link to="/comments" className="clear-inline-link">Open discussion</Link>
            </div>
          </article>

          <section className="metrics-grid metrics-grid-animated insights-metric-grid">
            {metrics.map((metric, index) => (
              <div key={metric.label} className="metric-card-stage" style={{ animationDelay: `${120 + index * 90}ms` }}>
                <MetricCard {...metric} />
              </div>
            ))}
          </section>
        </section>
      </section>
      ) : null}
    </section>
  );
}