import { toneOf } from "@/components/ui/verdict-tone";

// Privacy-safe share texts (Plan 6 F17), byte-identical to Android's for the
// same locale (packages/test-fixtures/share/*.json; the algorithm is in each
// fixture's "rules"). Only the product name, the grade, each chosen member's
// first name (or relation) and their status word are ever interpolated:
// never conditions, allergens, reason codes or nutrient totals.

/** The part of a next-intl translator this module uses. */
export type ShareTranslator = (
  key: string,
  values?: Record<string, string>,
) => string;

/** The VerdictOut fields a share may use (nothing else is read). */
export type ShareVerdict = {
  member_name: string;
  relation: string;
  status: string;
};

const RELATIONS = new Set(["self", "child", "parent", "spouse", "other"]);

/** First whitespace-separated word of the name; blank → the relation label. */
export function shareWho(
  t: ShareTranslator,
  v: Pick<ShareVerdict, "member_name" | "relation">,
): string {
  const first = v.member_name.trim().split(/\s+/)[0] ?? "";
  if (first !== "") return first;
  const relation = RELATIONS.has(v.relation) ? v.relation : "other";
  return t(`share.relation.${relation}`);
}

/** One member's part: "{who}: {status}" (an unexpected status reads unknown). */
export function shareMemberText(t: ShareTranslator, v: ShareVerdict): string {
  return t("share.result.member", {
    who: shareWho(t, v),
    status: t(`verdict.status.${toneOf(v.status)}`),
  });
}

/**
 * Ruling SH1: the share link is appended only when a site URL is configured
 * (`share.link`); without one the text has no link at all.
 */
function withLink(
  t: ShareTranslator,
  body: string,
  url: string | null,
): string {
  return url ? `${body} ${t("share.link", { url })}` : body;
}

/**
 * The result share text. `response.verdicts` are the members the user ticked,
 * in response order; with none ticked (the default, ruling SH1) the text names
 * the product and its grade only. `url` is null when no site URL is set.
 */
export function shareResultText(
  t: ShareTranslator,
  response: { grade: string | null; verdicts: readonly ShareVerdict[] },
  productName: string,
  url: string | null,
): string {
  const graded = response.grade !== null && response.grade !== "";
  if (response.verdicts.length === 0) {
    const body = graded
      ? t("share.result.product_only", {
          product: productName,
          grade: response.grade as string,
        })
      : t("share.result.product_only_ungraded", { product: productName });
    return withLink(t, body, url);
  }
  // Joined with ", " in every locale (fixture rule).
  const members = response.verdicts
    .map((v) => shareMemberText(t, v))
    .join(", ");
  const body = graded
    ? t("share.result.text", {
        product: productName,
        grade: response.grade as string,
        members,
      })
    : t("share.result.ungraded", { product: productName, members });
  return withLink(t, body, url);
}

/** The weekly share: counts only, as plain Latin-digit strings. */
export function shareWeeklyText(
  t: ShareTranslator,
  scans: number,
  logged: number,
  url: string | null,
): string {
  return withLink(
    t,
    t("share.weekly", { scans: String(scans), logged: String(logged) }),
    url,
  );
}

/**
 * The link in a share: the public product page for a barcoded product (generic
 * info only), else the site root, both in the UI locale. Null when
 * NEXT_PUBLIC_SITE_URL is not set (ruling SH1: never a guessed or hard-coded
 * domain, not even the page's own origin).
 */
export function shareUrl(
  locale: string,
  barcode: string | null,
): string | null {
  const origin = (process.env.NEXT_PUBLIC_SITE_URL ?? "")
    .trim()
    .replace(/\/+$/, "");
  if (!origin) return null;
  return barcode
    ? `${origin}/${locale}/p/${encodeURIComponent(barcode)}`
    : `${origin}/${locale}`;
}
