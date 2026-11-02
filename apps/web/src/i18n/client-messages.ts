import type { AbstractIntlMessages } from "next-intl";

// Namespaces that carry the verdict/health catalogue. Client components that
// render verdicts wrap themselves in their own NextIntlClientProvider with these;
// everyone else (including anonymous public pages) never receives them.
const SERVER_ONLY = new Set([
  "verdict",
  "status",
  "reason",
  "reason_variant",
  "nutrient",
  "allergen",
  "diet",
  "condition",
  "claim_verdict",
  "claim_reason",
]);

export function clientMessages(
  messages: AbstractIntlMessages,
): AbstractIntlMessages {
  return Object.fromEntries(
    Object.entries(messages).filter(([ns]) => !SERVER_ONLY.has(ns)),
  );
}
