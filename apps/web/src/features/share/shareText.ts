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
 * The result share text. `response.verdicts` are the members the user chose,
 * in response order; with none chosen the text names the product only.
 */
export function shareResultText(
  t: ShareTranslator,
  response: { grade: string | null; verdicts: readonly ShareVerdict[] },
  productName: string,
  url: string,
): string {
  const graded = response.grade !== null && response.grade !== "";
  if (response.verdicts.length === 0) {
    return graded
      ? t("share.result.product_only", {
          product: productName,
          grade: response.grade as string,
          url,
        })
      : t("share.result.product_only_ungraded", { product: productName, url });
  }
  // Joined with ", " in every locale (fixture rule).
  const members = response.verdicts
    .map((v) => shareMemberText(t, v))
    .join(", ");
  return graded
    ? t("share.result.text", {
        product: productName,
        grade: response.grade as string,
        members,
        url,
      })
    : t("share.result.ungraded", { product: productName, members, url });
}

/** The weekly share: counts only, as plain Latin-digit strings. */
export function shareWeeklyText(
  t: ShareTranslator,
  scans: number,
  logged: number,
  url: string,
): string {
  return t("share.weekly", {
    scans: String(scans),
    logged: String(logged),
    url,
  });
}

/**
 * The link in a share: the public product page for a barcoded product (generic
 * info only), else the site root, both in the UI locale.
 */
export function shareUrl(locale: string, barcode: string | null): string {
  const origin = (
    process.env.NEXT_PUBLIC_SITE_URL ||
    (typeof window !== "undefined" ? window.location.origin : "")
  ).replace(/\/+$/, "");
  return barcode
    ? `${origin}/${locale}/p/${encodeURIComponent(barcode)}`
    : `${origin}/${locale}`;
}
