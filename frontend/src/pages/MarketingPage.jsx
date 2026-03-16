import { Link } from "react-router-dom";
import ClickWordmark from "../components/ClickWordmark.jsx";

const pageContent = {
  product: {
    eyebrow: "Product",
    title: "Everything your team needs in one operating system",
    subtitle: "Plan projects, run tasks, centralize docs, and coordinate updates from one clear workflow.",
    highlights: [
      { title: "Tasks that move", text: "Use clear statuses, ownership, and due dates so progress is never hidden." },
      { title: "Work in context", text: "Comments, attachments, and activity stay attached to the right task." },
      { title: "Role-aware control", text: "Admins govern, managers execute, and contributors stay focused." }
    ],
    outcomes: ["48% faster task completion", "32% fewer status meetings", "Single source of truth across teams"],
    useCases: ["Sprint planning", "Release tracking", "Cross-functional launch workflows"],
    faq: {
      q: "Can we replace multiple tools with this setup?",
      a: "Yes. Teams usually centralize task tracking, updates, and collaboration into one workspace to reduce context switching."
    }
  },
  solutions: {
    eyebrow: "Solutions",
    title: "Built for marketing, product, operations, and support",
    subtitle: "Use one platform across teams while preserving role-specific visibility and controls.",
    highlights: [
      { title: "Marketing", text: "Run campaigns with calendar, status lanes, and review checkpoints." },
      { title: "Product", text: "Track releases, feedback, and launch blockers in one task graph." },
      { title: "Operations", text: "Standardize execution with templates, governance, and audit logs." }
    ],
    outcomes: ["Team-specific workflows", "Shared visibility without clutter", "Role-driven actions per department"],
    useCases: ["Campaign operations", "Product delivery", "Support escalation control"],
    faq: {
      q: "Can every team keep their own process?",
      a: "Absolutely. Each team can shape views and workflows while leaders still see unified progress at organization level."
    }
  },
  learn: {
    eyebrow: "Learn",
    title: "Get productive in minutes, not weeks",
    subtitle: "Follow guided playbooks and onboarding paths for every role in your workspace.",
    highlights: [
      { title: "Quick start guides", text: "Step-by-step onboarding for admins, managers, and contributors." },
      { title: "Best-practice templates", text: "Use proven workflows for sprint planning, launch ops, and support." },
      { title: "Role learning paths", text: "Short modules to teach how to use each screen with confidence." }
    ],
    outcomes: ["Faster onboarding", "Better process adoption", "Less confusion for first-time users"],
    useCases: ["New member onboarding", "Manager enablement", "Workspace rollout training"],
    faq: {
      q: "How quickly can new users become productive?",
      a: "Most teams complete onboarding in the first day using role-specific guidance and ready-to-use templates."
    }
  },
  pricing: {
    eyebrow: "Pricing",
    title: "Simple pricing that scales with your team",
    subtitle: "Start free, then unlock automation, advanced security, and enterprise governance when ready.",
    highlights: [
      { title: "Free", text: "Core project and task management for small teams." },
      { title: "Growth", text: "Advanced views, reporting, and collaboration controls." },
      { title: "Scale", text: "Security, SSO, audit depth, and organization-wide governance." }
    ],
    outcomes: ["Predictable cost model", "Upgrade only when needed", "Value aligned with team maturity"],
    useCases: ["Startup teams", "Scaling businesses", "Multi-org operations"],
    faq: {
      q: "Can we start free and upgrade later?",
      a: "Yes. Start with core capabilities and move to higher plans as your collaboration and governance needs grow."
    }
  },
  enterprise: {
    eyebrow: "Enterprise",
    title: "Enterprise-grade reliability and governance",
    subtitle: "Secure, scalable execution system with auditability and centralized control.",
    highlights: [
      { title: "Security", text: "Granular permissions, secure auth flows, and policy-ready controls." },
      { title: "Governance", text: "Track every critical change with structured activity timelines." },
      { title: "Scale", text: "Support complex org structures with consistent operational clarity." }
    ],
    outcomes: ["Enterprise security posture", "Auditable operations", "Consistent execution at scale"],
    useCases: ["Regulated environments", "Large global teams", "Centralized PMO governance"],
    faq: {
      q: "Is this ready for enterprise compliance needs?",
      a: "Yes. It is built to support strict access controls, traceability, and governance required by enterprise teams."
    }
  }
};

export default function MarketingPage({ pageKey = "product" }) {
  const page = pageContent[pageKey] || pageContent.product;

  return (
    <section className="marketing-page-shell">
      <header className="marketing-topbar">
        <Link to="/dashboard" className="marketing-brand-link" aria-label="Go to dashboard preview">
          <ClickWordmark className="click-wordmark-preview-header" />
        </Link>
        <nav className="marketing-nav" aria-label="Marketing pages">
          <Link to="/product" className={`marketing-nav-link${pageKey === "product" ? " active" : ""}`}>Product</Link>
          <Link to="/solutions" className={`marketing-nav-link${pageKey === "solutions" ? " active" : ""}`}>Solutions</Link>
          <Link to="/learn" className={`marketing-nav-link${pageKey === "learn" ? " active" : ""}`}>Learn</Link>
          <Link to="/pricing" className={`marketing-nav-link${pageKey === "pricing" ? " active" : ""}`}>Pricing</Link>
          <Link to="/enterprise" className={`marketing-nav-link${pageKey === "enterprise" ? " active" : ""}`}>Enterprise</Link>
        </nav>
        <div className="marketing-auth-actions">
          <Link to="/register" className="btn btn-secondary">Sign up</Link>
          <Link to="/login" className="btn btn-primary">Log in</Link>
        </div>
      </header>

      <section className="marketing-hero panel">
        <p className="eyebrow">{page.eyebrow}</p>
        <h1>{page.title}</h1>
        <p className="hero-subtitle">{page.subtitle}</p>
        <div className="landing-cta-row">
          <Link to="/register" className="btn marketing-btn-primary">Get started</Link>
          <Link to="/dashboard" className="btn marketing-btn-secondary">Back to preview</Link>
        </div>
      </section>

      <section className="marketing-grid">
        {page.highlights.map((item, index) => (
          <article key={item.title} className="marketing-card" style={{ animationDelay: `${100 + index * 90}ms` }}>
            <p className="section-label">0{index + 1}</p>
            <h3>{item.title}</h3>
            <p>{item.text}</p>
          </article>
        ))}
      </section>

      <section className="marketing-details-grid">
        <article className="marketing-detail-card">
          <p className="section-label">Why teams choose this</p>
          <h3>Measured outcomes</h3>
          <ul className="marketing-list">
            {page.outcomes.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="marketing-detail-card">
          <p className="section-label">Use cases</p>
          <h3>Where it performs best</h3>
          <ul className="marketing-list">
            {page.useCases.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="marketing-detail-card">
          <p className="section-label">FAQ</p>
          <h3>{page.faq.q}</h3>
          <p>{page.faq.a}</p>
        </article>
      </section>
    </section>
  );
}