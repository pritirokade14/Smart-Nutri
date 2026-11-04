"use client";

import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { AlertTriangleIcon } from "@/components/ui/icons";
import { track } from "@/lib/analytics";
import {
  REPORT_NOTE_MAX,
  REPORT_REASONS,
  type ReportReason,
  useCreateReport,
} from "../api/reports";

/**
 * "Report a problem" (F14) for a product in our catalogue: a reason, an
 * optional note (≤ 500, blank is not sent), then thanks. Reports go to
 * review; they never change a product or a result.
 */
export function ReportDialog({
  productId,
  onClose,
}: {
  productId: string;
  onClose: () => void;
}) {
  const t = useTranslations("report");
  const te = useTranslations("error");
  const tc = useTranslations("common");
  const noteId = useId();
  const [reason, setReason] = useState<ReportReason | null>(null);
  const [note, setNote] = useState("");
  const report = useCreateReport(productId);

  const submit = () => {
    if (!reason) return;
    const trimmed = note.trim();
    report.mutate(trimmed ? { reason, note: trimmed } : { reason }, {
      // The reason is a closed enum; the note never leaves the API call.
      onSuccess: () => track("report_submitted", { reason }),
    });
  };

  if (report.isSuccess)
    return (
      <Dialog
        title={t("title")}
        onClose={onClose}
        testId="report-dialog"
        actions={<Button onClick={onClose}>{tc("close")}</Button>}
      >
        <p role="status" className="text-md text-text-primary">
          {t("thanks")}
        </p>
      </Dialog>
    );

  const errorKey = report.error ? `${report.error.code}` : null;
  return (
    <Dialog
      title={t("title")}
      onClose={onClose}
      testId="report-dialog"
      actions={
        <>
          <Button variant="outline" onClick={onClose}>
            {tc("cancel")}
          </Button>
          <Button disabled={!reason || report.isPending} onClick={submit}>
            {t("submit")}
          </Button>
        </>
      }
    >
      <fieldset className="space-y-2">
        <legend className={labelClass}>{t("reason_label")}</legend>
        {REPORT_REASONS.map((r) => (
          <label
            key={r}
            className="flex min-h-11 cursor-pointer items-center gap-3 rounded-md border border-border-default px-3 text-md text-text-primary has-[:checked]:border-brand-primary"
          >
            <input
              type="radio"
              name="report-reason"
              value={r}
              checked={reason === r}
              onChange={() => setReason(r)}
              className="size-5 shrink-0"
            />
            {t(`reason.${r}`)}
          </label>
        ))}
      </fieldset>
      <div className="space-y-1">
        <label htmlFor={noteId} className={labelClass}>
          {t("note_label")}
        </label>
        <textarea
          id={noteId}
          value={note}
          maxLength={REPORT_NOTE_MAX}
          rows={3}
          onChange={(e) => setNote(e.target.value)}
          className={inputClass}
        />
        <p className={hintClass}>{t("note_hint")}</p>
      </div>
      {errorKey ? (
        <p role="alert" className="text-md text-text-primary">
          {te.has(errorKey) ? te(errorKey) : te("internal_error")}
        </p>
      ) : null}
    </Dialog>
  );
}

/** The "Report a problem" button and its dialog. */
export function ReportButton({ productId }: { productId: string }) {
  const t = useTranslations("report");
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button variant="ghost" size="sm" onClick={() => setOpen(true)}>
        <AlertTriangleIcon className="size-4" />
        {t("button")}
      </Button>
      {open ? (
        <ReportDialog productId={productId} onClose={() => setOpen(false)} />
      ) : null}
    </>
  );
}
