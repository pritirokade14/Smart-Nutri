import { useTranslations } from "next-intl";
import { Card } from "@/components/ui/Card";
import {
  AlertTriangleIcon,
  CheckCircleIcon,
  QuestionCircleIcon,
} from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";
import type { Translator } from "../lib/reasons";
import { type ClaimCheck, claimReasonText } from "../lib/report";

// A claim check is about the pack's wording, not about a person: it never
// uses the green "ok" tone. Supported stays neutral, contradicted is flagged
// with the caution tone and unverifiable is the unknown grey (same as
// Android's ClaimsSection).
const LOOK = {
  supported: { Icon: CheckCircleIcon, tone: undefined },
  contradicted: { Icon: AlertTriangleIcon, tone: "caution" },
  unverifiable: { Icon: QuestionCircleIcon, tone: "unknown" },
} as const;

/**
 * "Claims on the label, checked by SmartNutri": each front-of-pack claim
 * with the API's check. Renders nothing when no claim has a label here.
 */
export function ClaimsSection({ checks }: { checks: readonly ClaimCheck[] }) {
  const t = useTranslations();
  const shown = checks.filter((c) => t.has(`claim.${c.claim}`));
  if (shown.length === 0) return null;
  return (
    <Card as="section" className="space-y-4" data-testid="claims-section">
      <SectionHeader title={t("product.claims_heading")} />
      <ul className="space-y-3">
        {shown.map((c) => {
          const { Icon, tone } = LOOK[c.verdict];
          const reason = claimReasonText(t as unknown as Translator, c);
          return (
            <li
              key={c.claim}
              data-claim={c.claim}
              data-claim-verdict={c.verdict}
              className="flex gap-3 rounded-md border border-border-default p-3"
            >
              <span
                data-verdict={tone}
                className={
                  tone ? "text-(--verdict-color)" : "text-text-secondary"
                }
              >
                <Icon className="mt-0.5 size-5 shrink-0" />
              </span>
              <div className="min-w-0 space-y-1">
                <p className="text-md font-semibold text-text-primary">
                  {t("product.label_says", { claim: t(`claim.${c.claim}`) })}
                </p>
                <p className="text-md font-medium text-text-primary">
                  {t(`claim_verdict.${c.verdict}`)}
                </p>
                {reason ? (
                  <p className="text-sm text-text-secondary">{reason}</p>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
