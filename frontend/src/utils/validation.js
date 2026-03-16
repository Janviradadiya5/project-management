const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isUuid(value) {
  return UUID_REGEX.test(String(value || "").trim());
}

export function isNonEmpty(value, minLength = 1) {
  return String(value || "").trim().length >= minLength;
}

export function isValidAttachmentSize(value) {
  const num = Number(value);
  return Number.isInteger(num) && num > 0 && num <= 26214400;
}