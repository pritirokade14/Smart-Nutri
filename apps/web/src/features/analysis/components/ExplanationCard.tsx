import { useTranslations } from "next-intl";
import { Card } from "@/components/ui/Card";
import { SparkleIcon } from "@/components/ui/icons";
import { type ExplanationOut, explanationToShow } from "../lib/explanation";
import type { VerdictOut } from "../lib/reasons";

/**
 * The AI explanation (F7), labelled as AI. It explains the verdicts above and
 * never changes them, so it has a neutral style (no verdict colour). Hidden
 * when the API sends `unavailable` (no ai_processing consent, or the model
 * failed or disagreed with the engine) or when a member token can't be
 * resolved. "Information, not medical advice" is shown once per result view.
 */
export function ExplanationCard({
  explanation,
  verdicts,
}: {
  explanation: ExplanationOut | null | undefined;
  verdicts: readonly VerdictOut[];
}) {
  const t = useTranslations();
  const shown = explanationToShow(explanation, verdicts, t("result.you"));
  if (!shown) return null;
  return (
    <Card
      as="section"
      aria-labelledby="explanation-title"
      data-testid="explanation-card"
      className="space-y-3"
    >
      <header className="flex items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-soft text-brand-primary">
          <SparkleIcon />
        </span>
        <div className="min-w-0 space-y-0.5">
          <h2
            id="explanation-title"
            className="text-lg font-semibold text-text-primary"
          >
            {t("explanation.title")}
          </h2>
          <p data-testid="ai-note" className="text-sm text-text-secondary">
            {t("explanation.ai_note")}
          </p>
        </div>
      </header>
      {shown.text ? (
        <p className="text-md whitespace-pre-line text-text-primary">
          {shown.text}
        </p>
      ) : null}
      {shown.tips.length > 0 ? (
        <section className="space-y-2">
          <h3 className="text-md font-semibold text-text-primary">
            {t("explanation.tips_title")}
          </h3>
          <ul className="list-disc space-y-1 ps-5 text-md text-text-primary">
            {shown.tips.map((tip, i) => (
              // Tips have no id; API order is stable for one response.
              // biome-ignore lint/suspicious/noArrayIndexKey: see above
              <li key={i}>{tip}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </Card>
  );
}
