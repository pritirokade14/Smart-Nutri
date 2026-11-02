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

// What the logged-in verdict UI (ResultView, VerdictCard) needs on top of the
// root client catalogue. `condition` is not needed: condition_unrecognised
// carries the member's own wording (packages/i18n README, rule 2).
const RESULT_NAMESPACES = [
  "verdict",
  "status",
  "reason",
  "reason_variant",
  "nutrient",
  "allergen",
  "diet",
] as const;

/** Client catalogue for the result page: clientMessages + the verdict namespaces. */
export function resultMessages(
  messages: AbstractIntlMessages,
): AbstractIntlMessages {
  const picked = Object.fromEntries(
    RESULT_NAMESPACES.filter((ns) => ns in messages).map((ns) => [
      ns,
      messages[ns],
    ]),
  );
  return { ...clientMessages(messages), ...picked };
}
