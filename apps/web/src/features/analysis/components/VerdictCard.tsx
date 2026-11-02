import { useTranslations } from "next-intl";
import { displayReasons, type VerdictOut } from "../lib/reasons";
import { ReasonLine } from "./ReasonLine";

/**
 * One member's verdict, exactly as the API returned it. The colour comes from
 * CSS keyed on data-status (globals.css: .verdict-card → --color-verdict-*),
 * so the browser never picks or changes a verdict colour.
 */
export function VerdictCard({ verdict }: { verdict: VerdictOut }) {
  const t = useTranslations();
  const name = verdict.member_name.trim() || t("result.you");
  const statusKey = `status.${verdict.status}`;
  const [top, ...rest] = displayReasons(verdict.reasons);

  return (
    <article
      data-testid="verdict-card"
      data-status={verdict.status}
      className="verdict-card space-y-(--spacing-2) rounded-(--radius-md) border p-(--spacing-4)"
    >
      <header className="flex flex-wrap items-center justify-between gap-(--spacing-2)">
        <h2 className="text-(length:--text-lg)">
          {t("result.for_member", { name })}
        </h2>
        <span className="verdict-badge rounded-(--radius-sm) px-(--spacing-2) py-(--spacing-1) text-(length:--text-md) font-semibold">
          {t.has(statusKey) ? t(statusKey) : t("status.unknown")}
        </span>
      </header>
      {top && rest.length > 0 ? (
        <details className="text-(length:--text-md)">
          <summary className="cursor-pointer">
            <ReasonLine reason={top} />
          </summary>
          <ul className="mt-(--spacing-2) list-disc space-y-(--spacing-1) ps-(--spacing-5)">
            {rest.map((r, i) => (
              // Reasons have no id; API order is stable for one response.
              // biome-ignore lint/suspicious/noArrayIndexKey: see above
              <li key={`${i}-${r.code}`}>
                <ReasonLine reason={r} />
              </li>
            ))}
          </ul>
        </details>
      ) : top ? (
        <p className="text-(length:--text-md)">
          <ReasonLine reason={top} />
        </p>
      ) : null}
    </article>
  );
}
