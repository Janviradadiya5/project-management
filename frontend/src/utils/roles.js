const ROLE_LABELS = {
  super_admin: "Super Admin",
  organization_admin: "Organization Admin",
  project_manager: "Project Manager",
  team_member: "Team Member",
  viewer: "Viewer",
  manager: "Manager",
  contributor: "Contributor",
  guest: "Guest"
};

const ROLE_TONES = {
  super_admin: "elevated",
  organization_admin: "elevated",
  project_manager: "active",
  team_member: "active",
  viewer: "calm",
  manager: "active",
  contributor: "active",
  guest: "calm"
};

export function getEffectiveRole(roleCode, isSuperAdmin = false) {
  if (isSuperAdmin) {
    return "super_admin";
  }

  return roleCode || "guest";
}

export function getRoleLabel(roleCode, isSuperAdmin = false) {
  const effectiveRole = getEffectiveRole(roleCode, isSuperAdmin);
  return ROLE_LABELS[effectiveRole] || "Workspace Member";
}

export function getRoleTone(roleCode, isSuperAdmin = false) {
  const effectiveRole = getEffectiveRole(roleCode, isSuperAdmin);
  return ROLE_TONES[effectiveRole] || "calm";
}

export function canManageOrganization(roleCode, isSuperAdmin = false) {
  const effectiveRole = getEffectiveRole(roleCode, isSuperAdmin);
  return effectiveRole === "super_admin" || effectiveRole === "organization_admin";
}

export function canManageProjects(roleCode, isSuperAdmin = false) {
  const effectiveRole = getEffectiveRole(roleCode, isSuperAdmin);
  return ["super_admin", "organization_admin", "project_manager"].includes(effectiveRole);
}

export function canContribute(roleCode, isSuperAdmin = false) {
  const effectiveRole = getEffectiveRole(roleCode, isSuperAdmin);
  return ["super_admin", "organization_admin", "project_manager", "team_member"].includes(effectiveRole);
}

export function canReadWorkspace(roleCode, isSuperAdmin = false) {
  return getEffectiveRole(roleCode, isSuperAdmin) !== "guest";
}

export function canViewMembers(roleCode, isSuperAdmin = false) {
  const effectiveRole = getEffectiveRole(roleCode, isSuperAdmin);
  return ["super_admin", "organization_admin", "project_manager"].includes(effectiveRole);
}

export function canViewActivityLogs(roleCode, isSuperAdmin = false) {
  const effectiveRole = getEffectiveRole(roleCode, isSuperAdmin);
  return ["super_admin", "organization_admin", "project_manager"].includes(effectiveRole);
}
