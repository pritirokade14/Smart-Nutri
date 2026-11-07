import { useEffect, useMemo, useState } from "react";
import type { MemberOut } from "@/features/members/api/members";
import type { GoalSettingsOut, TargetsOut } from "../api/targets";
import {
  type GuideValues,
  initialValues,
  memberPatch,
  previewBody,
  settingsBody,
} from "../lib/guideForm";
import { usePreviewTargets, useSaveGuide } from "./useTargets";

/**
 * The guide form's state, shared by the setup stepper and the settings page.
 * While `previewing`, every change asks `targets_preview` for the numbers (the
 * engine decides; nothing is computed here). `save` is the members PATCH then
 * the settings PUT.
 */
export function useGuideForm({
  member,
  settings,
  previewing,
}: {
  member: MemberOut;
  settings: GoalSettingsOut | null;
  previewing: boolean;
}) {
  const [values, setValues] = useState<GuideValues>(() =>
    initialValues(member, settings),
  );
  const [unusualConfirmed, setUnusualConfirmed] = useState(false);
  const preview = usePreviewTargets();
  const saveGuide = useSaveGuide();
  const { mutate } = preview;

  const body = useMemo(() => previewBody(values, settings), [values, settings]);
  const key = JSON.stringify(body);
  // biome-ignore lint/correctness/useExhaustiveDependencies: `key` is the serialised `body`
  useEffect(() => {
    if (previewing) mutate(body);
  }, [key, previewing, mutate]);

  const set = <K extends keyof GuideValues>(k: K, v: GuideValues[K]) => {
    saveGuide.reset();
    setUnusualConfirmed(false);
    setValues((prev) => ({ ...prev, [k]: v }));
  };

  const targets: TargetsOut | undefined = preview.data;
  return {
    values,
    set,
    preview,
    targets,
    /** The pace in use: the chosen one, else the API's default. */
    selectedRate: values.rate ?? targets?.rate?.pct_bw_per_week ?? null,
    unusualConfirmed,
    setUnusualConfirmed,
    saveGuide,
    save: (): Promise<TargetsOut> =>
      saveGuide.mutateAsync({
        memberId: member.id,
        member: memberPatch(values, member),
        settings: settingsBody(values, settings),
      }),
    retryPreview: () => mutate(body),
  };
}
