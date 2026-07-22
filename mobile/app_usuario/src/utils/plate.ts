export const PLATE_REGEX = /^[A-Z]{3}-\d{4}$/;

export function maskPlateInput(raw: string): string {
  const cleaned = raw.toUpperCase().replace(/[^A-Z0-9]/g, "");
  const letters = (cleaned.match(/[A-Z]/g) ?? []).join("").slice(0, 3);
  const digits = (cleaned.match(/[0-9]/g) ?? []).join("").slice(0, 4);
  return digits ? `${letters}-${digits}` : letters;
}
