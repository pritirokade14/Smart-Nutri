"use client";

import { useLocale, useTranslations } from "next-intl";
import { type ReactNode, useEffect, useRef, useState } from "react";
import { Button, buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { chipClass } from "@/components/ui/Chip";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { ErrorState } from "@/components/ui/ErrorState";
import { InfoIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState } from "@/components/ui/Skeleton";
import { OffAttribution } from "@/features/analysis/components/OffAttribution";
import { BandBadge } from "@/features/history/components/BandBadge";
import {
  type Band,
  bandOf,
  shownBand,
  shownTotal,
} from "@/features/history/lib/summary";
import { isIsoDate } from "@/features/meals/api/meals";
import {
  ConsentDialog,
  errorKey,
} from "@/features/members/components/ConsentDialog";
import { EyeToggle } from "@/features/targets/components/EyeToggle";
import {
  useGoalSettings,
  useSetDisplay,
} from "@/features/targets/hooks/useTargets";
import { statusMessage } from "@/features/targets/lib/status";
import { track } from "@/lib/analytics";
import { cn } from "@/lib/cn";
import type { DiaryDayOut, MealOut } from "../api/diary";
import { useDiaryDay } from "../hooks/useDiaryDay";
import { useMealSlots } from "../hooks/useMealSlots";
import { clearDiaryAddContext } from "../lib/addContext";
import { slotLabel } from "../lib/slotLabel";
import { AddFoodPanel } from "./AddFoodPanel";
import { CopyDialog, type CopyKind } from "./CopyDialog";
import { DayHeader } from "./DayHeader";
import { DayMenu } from "./DayMenu";
import { DiaryRings, type SummaryView } from "./DiaryRings";
import { EditEntryDialog } from "./EditEntryDialog";
import { SlotSection } from "./SlotSection";
import { WeekView } from "./WeekView";

/** A sugar or salt band: an API band is kept; an unknown or incomplete total never reads "within limit". */
function limitBand(day: DiaryDayOut, key: "sugars_g" | "salt_g"): Band {
  const band =
    key === "sugars_g" ? day.limits_bands.sugar_g : day.limits_bands.salt_g;
  if (day.numbers_hidden.macros) return bandOf(band);
  const total = shownTotal(day.totals[key], day.incomplete[key]);
  const b = shownBand(band, total);
  return day.incomplete[key] && b === "ok" ? "unknown" : b;
}

function Summary({
  day,
  view,
  onView,
  canToggle,
}: {
  day: DiaryDayOut;
  view: SummaryView;
  onView: (v: SummaryView) => void;
  canToggle: boolean;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const ready = day.targets_status === "ready";
  const message =
    day.targets &&
    day.targets_status !== "ready" &&
    day.targets_status !== "none"
      ? statusMessage(t, day.targets)
      : null;
  return (
    <Card as="section" className="space-y-4" data-testid="diary-summary">
      {ready && canToggle && day.remaining !== null ? (
        <Button
          variant="secondary"
          size="sm"
          data-testid="summary-view-chip"
          onClick={() =>
            onView(view === "remaining" ? "consumed" : "remaining")
          }
        >
          {t(view === "remaining" ? "diary.remaining" : "diary.consumed")}
        </Button>
      ) : null}
      {message ? (
        <div className="space-y-2" data-testid="diary-targets-message">
          <p className="text-md text-text-primary">{message}</p>
          {day.targets_status === "needs_body_data" ? (
            <a
              href={`/${locale}/profile/guide`}
              className="inline-flex min-h-11 items-center text-md font-semibold text-brand-primary underline-offset-4 hover:underline"
            >
              {t("settings.diary.title")}
            </a>
          ) : null}
        </div>
      ) : null}
      <DiaryRings day={day} view={view} />
      <div className="flex flex-wrap gap-2" data-testid="diary-bands">
        {(["sugars_g", "salt_g"] as const).map((k) => (
          <span
            key={k}
            className="flex items-center gap-2 text-sm text-text-secondary"
          >
            {t(`summary.nutrient.${k}`)}
            <BandBadge band={limitBand(day, k)} />
          </span>
        ))}
      </div>
      {ready ? (
        <div className="space-y-1" data-testid="diary-target-footer">
          <p className="text-sm text-text-secondary">{t("diary.disclaimer")}</p>
          <p className="text-sm text-text-secondary">
            {t("targets.pending_review")}
          </p>
        </div>
      ) : null}
    </Card>
  );
}

function ConsentCard({ onAgreed }: { onAgreed: () => void }) {
  const t = useTranslations();
  const [asking, setAsking] = useState(false);
  return (
    <Card className="space-y-3" data-testid="diary-consent">
      <p className="text-md text-text-primary">{t("diary.targets_consent")}</p>
      <Button onClick={() => setAsking(true)}>{t("consent.agree")}</Button>
      {asking ? (
        <ConsentDialog
          onAgreed={() => {
            setAsking(false);
            onAgreed();
          }}
          onCancel={() => setAsking(false)}
        />
      ) : null}
    </Card>
  );
}

/**
 * The Diary day: the date switcher, the summary (energy ring, macro bars,
 * sugar and salt bands) and one section per meal slot. Everything shown is
 * what the API returned: no total, remaining, progress or target is computed
 * here. The web is online-only and says so.
 */
export function DiaryView({
  date: initialDate,
}: {
  /** From the page's `?date=`; anything but YYYY-MM-DD means the account's today. */
  date?: string;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const [date, setDate] = useState<string | undefined>(
    initialDate && isIsoDate(initialDate) ? initialDate : undefined,
  );
  const [editing, setEditing] = useState<MealOut | null>(null);
  const [view, setViewMode] = useState<"day" | "week">("day");
  const [adding, setAdding] = useState<{ slotId?: string } | null>(null);
  const [copying, setCopying] = useState<CopyKind | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const day = useDiaryDay(date);
  const settings = useGoalSettings();
  const slots = useMealSlots();
  const setDisplay = useSetDisplay();

  const viewed = useRef(false);
  useEffect(() => {
    if (viewed.current) return;
    viewed.current = true;
    track("diary_day_viewed");
    // Back on the Diary: an unfinished add-food trip no longer applies.
    clearDiaryAddContext();
  }, []);

  const pick = (next: string) => {
    setDate(next);
    try {
      const url = new URL(window.location.href);
      url.searchParams.set("date", next);
      window.history.replaceState(null, "", url);
    } catch {
      // The URL is a convenience only.
    }
  };

  const summaryView: SummaryView = settings.data?.summary_view ?? "remaining";
  const setView = (v: SummaryView) => setDisplay.mutate({ summary_view: v });

  let body: ReactNode;
  if (day.isPending) {
    body = <LoadingState label={t("common.loading")} />;
  } else if (day.isError) {
    body = (
      <ErrorState
        message={t(errorKey(t, day.error))}
        onRetry={() => void day.refetch()}
        retrying={day.isFetching}
      />
    );
  } else {
    const d = day.data;
    const hasEntries = d.slots.some((s) => s.entries.length > 0);
    const entries = d.slots.flatMap((s) => s.entries);
    const fromOff = entries.some((e) => e.attribution != null);
    const anyGrade = entries.some((e) => e.grade);
    body = (
      <div className="space-y-4">
        <DayHeader
          date={d.date}
          today={d.today}
          onDate={pick}
          trailing={
            settings.data ? (
              <EyeToggle targets={{ numbers_hidden: d.numbers_hidden }} />
            ) : null
          }
        />
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="space-y-4 lg:order-1" data-testid="diary-slots">
            <div
              className="flex flex-wrap items-center gap-2"
              data-testid="diary-toolbar"
            >
              <Button onClick={() => setAdding({})}>{t("diary.add")}</Button>
              <DayMenu
                day={d}
                onCopyYesterday={() =>
                  setCopying({ kind: "yesterday", toDate: d.date })
                }
                onCopyDay={() => setCopying({ kind: "day", toDate: d.date })}
              />
              {d.partial_logged ? (
                <span className={chipClass} data-testid="day-partial-badge">
                  {t("diary.partial_badge")}
                </span>
              ) : null}
            </div>
            {notice ? (
              <p
                role="status"
                data-testid="diary-notice"
                className="rounded-md bg-surface-muted px-3 py-2 text-md text-text-primary"
              >
                {notice}
              </p>
            ) : null}
            {!hasEntries ? (
              <p
                data-testid="diary-empty"
                className="text-md text-text-secondary"
              >
                {t("diary.empty_day")}
              </p>
            ) : null}
            {d.slots.map((s) => (
              <SlotSection
                key={s.slot_id}
                slot={s}
                onEdit={setEditing}
                actions={
                  <span className="flex items-center gap-1">
                    {s.entries.length > 0 ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          setCopying({
                            kind: "meal",
                            fromDate: d.date,
                            fromSlotId: s.slot_id,
                          })
                        }
                      >
                        {t("diary.copy_meal")}
                      </Button>
                    ) : null}
                    {!s.archived ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setAdding({ slotId: s.slot_id })}
                      >
                        {t("diary.add_to_slot", {
                          slot: slotLabel((k) => t(k), {
                            labelKey: s.label_key,
                            customLabel: s.custom_label,
                          }),
                        })}
                      </Button>
                    ) : null}
                  </span>
                }
              />
            ))}
            {anyGrade ? (
              <p className="text-sm text-text-secondary">
                {t("nutriscore.calculated_by")}
              </p>
            ) : null}
            {fromOff ? <OffAttribution barcode={null} /> : null}
          </div>
          <div className="space-y-4 lg:order-2">
            {d.targets_status === "consent_required" ? (
              <ConsentCard onAgreed={() => void day.refetch()} />
            ) : null}
            {d.targets_status === "none" ? (
              <Card className="space-y-3" data-testid="diary-no-guide">
                <p className="text-md text-text-primary">
                  {t("diary.no_guide")}
                </p>
                <a
                  href={`/${locale}/guide/setup`}
                  className={buttonClass({ variant: "primary" })}
                >
                  {t("targets.setup_cta")}
                </a>
              </Card>
            ) : null}
            <Summary
              day={d}
              view={summaryView}
              onView={setView}
              canToggle={Boolean(settings.data)}
            />
          </div>
        </div>
        {adding ? (
          <AddFoodPanel
            date={d.date}
            today={d.today}
            slotId={adding.slotId}
            onClose={() => setAdding(null)}
            onLogged={() => setAdding(null)}
          />
        ) : null}
        {copying ? (
          <CopyDialog
            target={copying}
            today={d.today}
            slots={slots.data?.items}
            onClose={() => setCopying(null)}
            onCopied={(n) => setNotice(t("diary.copied", { count: n }))}
          />
        ) : null}
        {editing ? (
          <EditEntryDialog
            key={editing.id}
            entry={editing}
            slots={slots.data?.items}
            onClose={() => setEditing(null)}
          />
        ) : null}
      </div>
    );
  }

  return (
    <main className="mx-auto w-full max-w-5xl space-y-6">
      <SectionHeader as="h1" title={t("diary.title")} />
      <p
        data-testid="online-only"
        className="flex items-start gap-2 rounded-md bg-surface-muted px-3 py-2 text-sm text-text-secondary"
      >
        <InfoIcon className="mt-0.5 size-4 shrink-0" />
        <span>{t("meals.online_only")}</span>
      </p>
      <fieldset
        className="m-0 flex min-w-0 gap-2 border-0 p-0"
        data-testid="diary-view-switch"
      >
        <legend className="sr-only">{t("diary.title")}</legend>
        {(["day", "week"] as const).map((v) => (
          <button
            key={v}
            type="button"
            aria-pressed={view === v}
            onClick={() => setViewMode(v)}
            className={cn(
              "min-h-9 cursor-pointer rounded-full px-4 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
              view === v
                ? "bg-brand-primary text-brand-on"
                : "bg-surface-muted text-text-primary",
            )}
          >
            {v === "day" ? t("diary.view.day") : t("diary.week.title")}
          </button>
        ))}
      </fieldset>
      {view === "week" ? (
        <WeekView
          today={day.data?.today}
          onPickDay={(d) => {
            pick(d);
            setViewMode("day");
          }}
        />
      ) : (
        body
      )}
      <DisclaimerFooter />
    </main>
  );
}
