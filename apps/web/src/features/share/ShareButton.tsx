"use client";

import { useTranslations } from "next-intl";
import { type ReactNode, useState } from "react";
import { Button, buttonClass } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { InfoIcon } from "@/components/ui/icons";
import { track } from "@/lib/analytics";

/**
 * Share: opens a sheet with the user's choices (children), a preview of the
 * exact text and the privacy note. With the Web Share API it hands the text
 * to the system share sheet (the text already ends with any link, so only
 * `text` is passed); without it, "Copy link" (only when there is a link,
 * ruling SH1) and a WhatsApp link. Analytics get the event name only, never
 * the text.
 */
export function ShareButton({
  label,
  text,
  url,
  event,
  children,
  variant = "outline",
}: {
  label: string;
  text: string;
  /** The link in the text; null when no site URL is configured. */
  url: string | null;
  /** Analytics event name (no properties). */
  event: string;
  /** What the user may include (e.g. one checkbox per member). */
  children?: ReactNode;
  variant?: "outline" | "secondary";
}) {
  const t = useTranslations();
  const [open, setOpen] = useState(false);
  const [native, setNative] = useState(false);
  const [copied, setCopied] = useState(false);

  function openSheet() {
    // Decided on the click, in the browser (never during server render).
    setNative(typeof navigator.share === "function");
    setCopied(false);
    setOpen(true);
  }

  async function shareNative() {
    try {
      await navigator.share({ text });
      track(event);
      setOpen(false);
    } catch {
      // Cancelled by the user, or refused: nothing was shared.
    }
  }

  async function copyLink() {
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      track(event);
    } catch {
      setCopied(false);
    }
  }

  return (
    <>
      <Button variant={variant} onClick={openSheet}>
        {label}
      </Button>
      {open ? (
        <Dialog
          title={label}
          onClose={() => setOpen(false)}
          testId="share-dialog"
          actions={
            native ? (
              <>
                <Button variant="outline" onClick={() => setOpen(false)}>
                  {t("common.cancel")}
                </Button>
                <Button onClick={shareNative}>{t("share.button")}</Button>
              </>
            ) : (
              <>
                {url ? (
                  <Button variant="outline" onClick={copyLink}>
                    {t("share.copy_link")}
                  </Button>
                ) : null}
                <a
                  href={`https://wa.me/?text=${encodeURIComponent(text)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => track(event)}
                  className={buttonClass()}
                >
                  {t("share.whatsapp")}
                </a>
                <Button variant="ghost" onClick={() => setOpen(false)}>
                  {t("common.close")}
                </Button>
              </>
            )
          }
        >
          {children}
          <section className="space-y-1">
            <h3 className="text-sm font-semibold text-text-secondary">
              {t("share.preview")}
            </h3>
            <p
              data-testid="share-preview"
              className="rounded-md border border-border-default bg-surface-muted px-3 py-2 text-md break-words whitespace-pre-wrap text-text-primary"
            >
              {text}
            </p>
          </section>
          <p className="flex items-start gap-2 text-sm text-text-secondary">
            <InfoIcon className="mt-0.5 size-4 shrink-0" />
            <span>{t("share.privacy_note")}</span>
          </p>
          {copied ? (
            <p role="status" className="text-md text-text-primary">
              {t("share.copied")}
            </p>
          ) : null}
        </Dialog>
      ) : null}
    </>
  );
}
