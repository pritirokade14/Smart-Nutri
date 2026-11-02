import { useLocale, useTranslations } from "next-intl";
import { type ReasonOut, reasonText, type Translator } from "../lib/reasons";

export function ReasonLine({ reason }: { reason: ReasonOut }) {
  const t = useTranslations() as unknown as Translator;
  const locale = useLocale();
  return (
    <span data-reason-code={reason.code} data-severity={reason.severity}>
      {reasonText(t, reason, locale)}
    </span>
  );
}
