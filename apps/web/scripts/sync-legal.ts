// Copies the policy drafts in docs/launch into the web app, so the public
// /[locale]/privacy and /[locale]/terms pages ship the reviewed text without
// the Docker build needing docs/. Run after editing a draft:
//   pnpm --filter @smartnutri/web sync:legal
// tests/features/legal/legal-content.test.ts fails while a copy is stale.
// Self-contained (node: imports only) so Node runs it with type stripping.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const LEGAL_DOCS = [
  { source: "privacy-policy.md", target: "privacy.ts" },
  { source: "terms.md", target: "terms.ts" },
] as const;

const WEB = join(dirname(fileURLToPath(import.meta.url)), "..");
export const DOCS_DIR = join(WEB, "../../docs/launch");
export const CONTENT_DIR = join(WEB, "src/content/legal");

/**
 * The module text for one draft. The leading blockquote is the editors'
 * note (review status, where the text is served, which code constant holds
 * the version); it is dropped, and its version is exported on its own.
 */
export function legalModule(markdown: string, source: string): string {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const start = lines.findIndex((l) => l.startsWith(">"));
  let end = start;
  while (end >= 0 && end < lines.length && lines[end]?.startsWith(">")) end++;
  const note = start >= 0 ? lines.slice(start, end).join("\n") : "";
  const version = /Version: `([^`]+)`/.exec(note)?.[1];
  if (!version) throw new Error(`${source}: no "Version: \`…\`" in the note`);
  const body = (
    start >= 0 ? [...lines.slice(0, start), ...lines.slice(end)] : lines
  )
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  return [
    `// GENERATED from docs/launch/${source} by scripts/sync-legal.ts. Do not edit.`,
    "",
    `export const version = ${JSON.stringify(version)};`,
    "",
    "export const markdown =",
    `  ${JSON.stringify(`${body}\n`)};`,
    "",
  ].join("\n");
}

function main(): void {
  for (const { source, target } of LEGAL_DOCS) {
    const md = readFileSync(join(DOCS_DIR, source), "utf8");
    writeFileSync(join(CONTENT_DIR, target), legalModule(md, source));
    console.log(`wrote src/content/legal/${target}`);
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main();
}
