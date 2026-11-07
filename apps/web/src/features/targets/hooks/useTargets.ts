import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { mealsKey } from "@/features/meals/api/meals";
import {
  type MemberPatch,
  membersKey,
  updateMember,
} from "@/features/members/api/members";
import type { ApiError } from "@/lib/api/errors";
import {
  type DisplayIn,
  deleteGoalSettings,
  type GoalSettingsIn,
  type GoalSettingsOut,
  getGoalSettings,
  getTodayTargets,
  goalSettingsKey,
  previewTargets,
  putDisplay,
  putGoalSettings,
  type TargetsOut,
  type TargetsPreviewIn,
  targetsKey,
  todayTargetsKey,
} from "../api/targets";

// Health data: never kept long once nobody is looking at it.
const HEALTH = { gcTime: 60_000, retry: false } as const;

/** Today's targets for the primary member, exactly as the API sent them. */
export function useTodayTargets(): UseQueryResult<TargetsOut, ApiError> {
  return useQuery<TargetsOut, ApiError>({
    queryKey: todayTargetsKey,
    queryFn: getTodayTargets,
    ...HEALTH,
  });
}

/** The stored guide settings (null: none yet). */
export function useGoalSettings(): UseQueryResult<
  GoalSettingsOut | null,
  ApiError
> {
  return useQuery<GoalSettingsOut | null, ApiError>({
    queryKey: goalSettingsKey,
    queryFn: getGoalSettings,
    ...HEALTH,
  });
}

/** Unsaved settings and body data in, the engine's numbers out. Stores nothing. */
export function usePreviewTargets(): UseMutationResult<
  TargetsOut,
  ApiError,
  TargetsPreviewIn
> {
  return useMutation<TargetsOut, ApiError, TargetsPreviewIn>({
    mutationFn: previewTargets,
    retry: false,
  });
}

export type SaveGuide = {
  /** The primary member to update first (body data); omitted: nothing to change. */
  memberId?: string;
  member?: MemberPatch;
  settings: GoalSettingsIn;
};

/**
 * Save the guide: members PATCH (body data), then settings PUT. Targets and
 * the meal summary are refreshed afterwards.
 */
export function useSaveGuide(): UseMutationResult<
  TargetsOut,
  ApiError,
  SaveGuide
> {
  const client = useQueryClient();
  return useMutation<TargetsOut, ApiError, SaveGuide>({
    mutationFn: async ({ memberId, member, settings }) => {
      if (memberId && member) await updateMember(memberId, member);
      return putGoalSettings(settings);
    },
    retry: false,
    onSuccess: () =>
      Promise.all([
        client.invalidateQueries({ queryKey: targetsKey }),
        client.invalidateQueries({ queryKey: mealsKey }),
        client.invalidateQueries({ queryKey: membersKey }),
      ]),
  });
}

function useRefreshTargets() {
  const client = useQueryClient();
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: targetsKey }),
      client.invalidateQueries({ queryKey: mealsKey }),
    ]);
}

/** The eye toggle and the Numbers setting (terms only). */
export function useSetDisplay(): UseMutationResult<
  GoalSettingsOut,
  ApiError,
  DisplayIn
> {
  const refresh = useRefreshTargets();
  return useMutation<GoalSettingsOut, ApiError, DisplayIn>({
    mutationFn: putDisplay,
    retry: false,
    onSuccess: refresh,
  });
}

/** Reset the daily guide (the food log stays). */
export function useResetGuide(): UseMutationResult<void, ApiError, void> {
  const refresh = useRefreshTargets();
  return useMutation<void, ApiError, void>({
    mutationFn: deleteGoalSettings,
    retry: false,
    onSuccess: refresh,
  });
}
