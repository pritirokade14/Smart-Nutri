import type { ReactNode } from "react";

// A small renderer for the policy drafts in docs/launch (no dependency): ATX
// headings, paragraphs (a line break stays a line break), "-" lists,
// numbered lists, pipe tables, block quotes, rules, and inline **bold**,
// `code` and [links](...). Links are kept only when they are site paths
// (sent through `localeHref`) or https; anything else renders as its text.
// No HTML is ever passed through.

type Block =
  | { kind: "heading"; level: number; text: string }
  | { kind: "paragraph"; lines: string[] }
  | { kind: "quote"; lines: string[] }
  | { kind: "list"; ordered: boolean; items: string[] }
  | { kind: "table"; head: string[]; rows: string[][] }
  | { kind: "rule" };

const HEADING = /^(#{1,4})\s+(.*)$/;
const BULLET = /^\s*[-*]\s+(.*)$/;
const NUMBERED = /^\s*\d+\.\s+(.*)$/;
const TABLE_SEPARATOR = /^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/;

function cells(row: string): string[] {
  return row
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((c) => c.trim());
}

export function parseBlocks(source: string): Block[] {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i] ?? "";
    if (line.trim() === "") {
      i++;
      continue;
    }
    const heading = HEADING.exec(line);
    if (heading) {
      blocks.push({
        kind: "heading",
        level: heading[1]?.length ?? 2,
        text: heading[2] ?? "",
      });
      i++;
      continue;
    }
    if (/^\s*(-{3,}|\*{3,})\s*$/.test(line)) {
      blocks.push({ kind: "rule" });
      i++;
      continue;
    }
    if (line.trimStart().startsWith("|")) {
      const rows: string[][] = [];
      while (i < lines.length && (lines[i] ?? "").trimStart().startsWith("|")) {
        if (!TABLE_SEPARATOR.test(lines[i] ?? ""))
          rows.push(cells(lines[i] ?? ""));
        i++;
      }
      blocks.push({ kind: "table", head: rows[0] ?? [], rows: rows.slice(1) });
      continue;
    }
    if (line.startsWith(">")) {
      const quoted: string[] = [];
      while (i < lines.length && (lines[i] ?? "").startsWith(">")) {
        quoted.push((lines[i] ?? "").replace(/^>\s?/, ""));
        i++;
      }
      blocks.push({ kind: "quote", lines: quoted.filter((l) => l !== "") });
      continue;
    }
    const ordered = NUMBERED.test(line);
    if (ordered || BULLET.test(line)) {
      const marker = ordered ? NUMBERED : BULLET;
      const items: string[] = [];
      while (i < lines.length) {
        const l = lines[i] ?? "";
        const m = marker.exec(l);
        if (m) items.push(m[1] ?? "");
        else if (/^\s{2,}\S/.test(l) && items.length > 0)
          items[items.length - 1] = `${items.at(-1)} ${l.trim()}`;
        else break;
        i++;
      }
      blocks.push({ kind: "list", ordered, items });
      continue;
    }
    const para: string[] = [];
    while (i < lines.length) {
      const l = lines[i] ?? "";
      if (
        l.trim() === "" ||
        HEADING.test(l) ||
        BULLET.test(l) ||
        NUMBERED.test(l) ||
        l.trimStart().startsWith("|") ||
        l.startsWith(">")
      )
        break;
      para.push(l.trim());
      i++;
    }
    blocks.push({ kind: "paragraph", lines: para });
  }
  return blocks;
}

const INLINE = /(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/;
const LINK = /^\[([^\]]+)\]\(([^)\s]+)\)$/;

const linkClass =
  "font-semibold text-brand-primary underline underline-offset-4 hover:text-brand-strong";

function inline(
  text: string,
  localeHref: (path: string) => string,
): ReactNode[] {
  const out: ReactNode[] = [];
  let key = 0;
  for (const part of text.split(INLINE)) {
    if (part === "") continue;
    key++;
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      out.push(
        <strong key={key} className="font-semibold text-text-primary">
          {inline(part.slice(2, -2), localeHref)}
        </strong>,
      );
    } else if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      out.push(
        <code
          key={key}
          className="rounded bg-surface-muted px-1 font-mono text-sm"
        >
          {part.slice(1, -1)}
        </code>,
      );
    } else if (LINK.test(part)) {
      const [, label = "", href = ""] = LINK.exec(part) ?? [];
      if (href.startsWith("/") && !href.startsWith("//")) {
        out.push(
          <a key={key} href={localeHref(href)} className={linkClass}>
            {label}
          </a>,
        );
      } else if (href.startsWith("https://")) {
        out.push(
          <a
            key={key}
            href={href}
            rel="noopener noreferrer"
            target="_blank"
            className={linkClass}
          >
            {label}
          </a>,
        );
      } else {
        out.push(part);
      }
    } else {
      out.push(part);
    }
  }
  return out;
}

function lines(
  rows: string[],
  localeHref: (path: string) => string,
): ReactNode[] {
  const out: ReactNode[] = [];
  let key = 0;
  for (const row of rows) {
    if (out.length > 0) out.push(<br key={`br${key}`} />);
    out.push(<span key={`l${key}`}>{inline(row, localeHref)}</span>);
    key++;
  }
  return out;
}

const HEADING_CLASS: Record<number, string> = {
  1: "text-2xl font-bold text-text-primary sm:text-3xl",
  2: "pt-4 text-xl font-semibold text-text-primary",
  3: "pt-2 text-lg font-semibold text-text-primary",
  4: "text-md font-semibold text-text-primary",
};

/** Renders trusted Markdown (the policy drafts) as plain elements. */
export function Markdown({
  source,
  localeHref,
}: {
  source: string;
  localeHref: (path: string) => string;
}) {
  const out: ReactNode[] = [];
  let key = 0;
  for (const b of parseBlocks(source)) {
    key++;
    switch (b.kind) {
      case "heading": {
        const Tag = `h${Math.min(b.level, 4)}` as "h1" | "h2" | "h3" | "h4";
        out.push(
          <Tag key={key} className={HEADING_CLASS[b.level] ?? HEADING_CLASS[4]}>
            {inline(b.text, localeHref)}
          </Tag>,
        );
        break;
      }
      case "paragraph":
        out.push(
          <p key={key} className="text-md text-text-primary">
            {lines(b.lines, localeHref)}
          </p>,
        );
        break;
      case "quote":
        out.push(
          <blockquote
            key={key}
            className="border-s-4 border-border-default ps-4 text-md text-text-secondary"
          >
            {lines(b.lines, localeHref)}
          </blockquote>,
        );
        break;
      case "list": {
        const Tag = b.ordered ? "ol" : "ul";
        const items: ReactNode[] = [];
        let n = 0;
        for (const item of b.items) {
          n++;
          items.push(<li key={n}>{inline(item, localeHref)}</li>);
        }
        out.push(
          <Tag
            key={key}
            className={`${b.ordered ? "list-decimal" : "list-disc"} space-y-1 ps-6 text-md text-text-primary`}
          >
            {items}
          </Tag>,
        );
        break;
      }
      case "table": {
        const head: ReactNode[] = [];
        let n = 0;
        for (const c of b.head) {
          n++;
          head.push(
            <th
              key={n}
              scope="col"
              className="border-b border-border-default px-3 py-2 text-start font-semibold"
            >
              {inline(c, localeHref)}
            </th>,
          );
        }
        const body: ReactNode[] = [];
        let r = 0;
        for (const row of b.rows) {
          r++;
          const tds: ReactNode[] = [];
          let c = 0;
          for (const cell of row) {
            c++;
            tds.push(
              <td
                key={c}
                className="border-b border-border-default px-3 py-2 align-top"
              >
                {inline(cell, localeHref)}
              </td>,
            );
          }
          body.push(<tr key={r}>{tds}</tr>);
        }
        out.push(
          <div key={key} className="overflow-x-auto">
            <table className="w-full border-collapse text-sm text-text-primary">
              <thead>
                <tr>{head}</tr>
              </thead>
              <tbody>{body}</tbody>
            </table>
          </div>,
        );
        break;
      }
      case "rule":
        out.push(<hr key={key} className="border-border-default" />);
        break;
    }
  }
  return <>{out}</>;
}
