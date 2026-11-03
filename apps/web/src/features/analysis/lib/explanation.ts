import type { components } from "@smartnutri/api-client";

export type ExplanationOut = components["schemas"]["ExplanationOut"];
type VerdictOut = components["schemas"]["VerdictOut"];

const ESCAPE = /[.*+?^${}()|[\]\\]/g;
const ANY_TOKEN = /member_\d+/;

/**
 * Replaces each `member_N` token with that member's display name, in one
 * pass. Tokens are tried longest first, so `member_10` is never read as
 * `member_1` + "0", and an inserted name is never substituted again. Returns
 * null when a token can't be resolved (unknown token, or a ref to a member
 * not in this result): the caller then hides the explanation.
 */
export function substituteMembers(
  text: string,
  refs: Record<string, string>,
  nameOf: (memberId: string) => string | null,
): string | null {
  const names = new Map<string, string>();
  for (const [token, id] of Object.entries(refs)) {
    if (!/^member_\d+$/.test(token)) continue;
    const name = nameOf(id);
    if (name !== null) names.set(token, name);
  }
  if (names.size === 0) return ANY_TOKEN.test(text) ? null : text;
  const tokens = [...names.keys()].sort((a, b) => b.length - a.length);
  const pattern = new RegExp(
    `(?<![A-Za-z0-9_])(${tokens.map((k) => k.replace(ESCAPE, "\\$&")).join("|")})(?![0-9])`,
    "g",
  );
  // Split on the tokens (odd parts are the captured tokens), so no inserted
  // name is ever scanned again; any token left in the text is unresolved.
  const parts = text.split(pattern);
  if (parts.some((p, i) => i % 2 === 0 && ANY_TOKEN.test(p))) return null;
  return parts.map((p, i) => (i % 2 === 1 ? names.get(p) : p)).join("");
}

export type ShownExplanation = { text: string | null; tips: string[] };

/**
 * What the explanation card shows, or null to hide it: hidden when the API
 * says `unavailable`, when there is nothing to show, or when any member token
 * can't be resolved. The account holder (or a member with no name) is
 * `you`; everyone else is their name as sent.
 */
export function explanationToShow(
  explanation: ExplanationOut | null | undefined,
  verdicts: readonly VerdictOut[],
  you: string,
): ShownExplanation | null {
  if (explanation?.source !== "llm") return null;
  const byId = new Map(verdicts.map((v) => [v.member_id, v]));
  const nameOf = (id: string) => {
    const v = byId.get(id);
    if (!v) return null;
    return v.is_primary || v.member_name === "" ? you : v.member_name;
  };
  const sub = (s: string) =>
    substituteMembers(s, explanation.member_refs ?? {}, nameOf);
  const raw = explanation.text?.trim() ? explanation.text : null;
  const text = raw === null ? null : sub(raw);
  if (raw !== null && text === null) return null;
  const tips: string[] = [];
  for (const tip of explanation.tips ?? []) {
    if (!tip.trim()) continue;
    const s = sub(tip);
    if (s === null) return null;
    tips.push(s);
  }
  if (text === null && tips.length === 0) return null;
  return { text, tips };
}
