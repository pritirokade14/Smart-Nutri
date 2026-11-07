import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { mealsKey } from "@/features/meals/api/meals";
import { useDeleteMeal } from "@/features/meals/hooks/useMeals";
import { targetsKey } from "@/features/targets/api/targets";
import type { ApiError } from "@/lib/api/errors";
import {
  type CopyIn,
  type CopyOut,
  copyMeals,
  type DiaryDayOut,
  type DiaryWeekOut,
  diaryDayKey,
  diaryWeekKey,
  getDiaryDay,
  getDiaryWeek,
  getRecents,
  type MealOut,
  type MealPatch,
  putDayStatus,
  type RecentsOut,
  recentsKey,
  updateMeal,
} from "../api/diary";

// Personal and health data: never kept long once nobody is looking at it.
const PERSONAL = { gcTime: 60_000, retry: false } as const;

export { useDeleteMeal };

export function useDiaryDay(
  date?: string,
): UseQueryResult<DiaryDayOut, ApiError> {
  return useQuery<DiaryDayOut, ApiError>({
    queryKey: diaryDayKey(date),
    queryFn: () => getDiaryDay(date),
    ...PERSONAL,
  });
}

export function useDiaryWeek(
  end?: string,
  enabled = true,
): UseQueryResult<DiaryWeekOut, ApiError> {
  return useQuery<DiaryWeekOut, ApiError>({
    queryKey: diaryWeekKey(end),
    queryFn: () => getDiaryWeek(end),
    enabled,
    ...PERSONAL,
  });
}

/** Never retried automatically: the user taps again. */
export function useUpdateMeal(): UseMutationResult<
  MealOut,
  ApiError,
  { id: string; patch: MealPatch }
> {
  const client = useQueryClient();
  return useMutation<MealOut, ApiError, { id: string; patch: MealPatch }>({
    mutationFn: ({ id, patch }) => updateMeal(id, patch),
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: mealsKey }),
  });
}

export function useSetPartial(): UseMutationResult<
  unknown,
  ApiError,
  { date: string; partial: boolean }
> {
  const client = useQueryClient();
  return useMutation<unknown, ApiError, { date: string; partial: boolean }>({
    mutationFn: ({ date, partial }) => putDayStatus(date, partial),
    retry: false,
    onSuccess: () =>
      Promise.all([
        client.invalidateQueries({ queryKey: mealsKey }),
        client.invalidateQueries({ queryKey: targetsKey }),
      ]),
  });
}

export function useRecents(
  slotId?: string,
  enabled = true,
): UseQueryResult<RecentsOut, ApiError> {
  return useQuery<RecentsOut, ApiError>({
    queryKey: recentsKey(slotId),
    queryFn: () => getRecents(slotId),
    enabled,
    ...PERSONAL,
  });
}

export function useCopyMeals(): UseMutationResult<CopyOut, ApiError, CopyIn> {
  const client = useQueryClient();
  return useMutation<CopyOut, ApiError, CopyIn>({
    mutationFn: copyMeals,
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: mealsKey }),
  });
}
