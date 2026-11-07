type T = (key: string) => string;

/**
 * A slot's display name. A custom label is the user's own text: it is shown
 * exactly as typed and never translated. Otherwise the default key is
 * translated.
 */
export function slotLabel(
  t: T,
  {
    labelKey,
    customLabel,
  }: { labelKey?: string | null; customLabel?: string | null },
): string {
  if (customLabel != null && customLabel !== "") return customLabel;
  return labelKey ? t(labelKey) : "";
}
