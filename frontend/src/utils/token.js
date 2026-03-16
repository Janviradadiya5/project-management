export function extractTokenFromValue(value) {
  const raw = String(value || "").trim();
  if (!raw) {
    return "";
  }

  try {
    const url = new URL(raw);
    return (
      url.searchParams.get("token")
      || url.searchParams.get("invite_token")
      || ""
    ).trim();
  } catch {
    return raw;
  }
}
