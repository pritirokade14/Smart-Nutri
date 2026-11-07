import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { mealsKey } from "@/features/meals/api/meals";
import { targetsKey } from "@/features/targets/api/targets";
import type { ApiError } from "@/lib/api/errors";
import {
  deleteWeight,
  getWeightTrend,
  listWeights,
  putWeight,
  type TrendDays,
  type WeightIn,
  type WeightOut,
  type WeightsOut,
  type WeightTrendOut,
  weightListKey,
  weightTrendKey,
} from "../api/weights";

// Health data: never kept long once nobody is looking at it.
const PERSONAL = { gcTime: 60_000, retry: false } as const;

export function useWeightTrend(
  days: TrendDays,
): UseQueryResult<WeightTrendOut, ApiError> {
  return useQuery<WeightTrendOut, ApiError>({
    queryKey: weightTrendKey(days),
    queryFn: () => getWeightTrend(days),
    ...PERSONAL,
  });
}

export function useWeightList(
  enabled = true,
): UseQueryResult<WeightsOut, ApiError> {
  return useQuery<WeightsOut, ApiError>({
    queryKey: weightListKey,
    queryFn: listWeights,
    enabled,
    ...PERSONAL,
  });
}

// A weigh-in can change today's targets (the trend weight) and the diary day.
function useRefresh() {
  const client = useQueryClient();
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: mealsKey }),
      client.invalidateQueries({ queryKey: targetsKey }),
    ]);
}

/** Never retried automatically: the user taps again (or "Save anyway"). */
export function useSaveWeight(): UseMutationResult<
  WeightOut,
  ApiError,
  { day: string; body: WeightIn }
> {
  const refresh = useRefresh();
  return useMutation<WeightOut, ApiError, { day: string; body: WeightIn }>({
    mutationFn: ({ day, body }) => putWeight(day, body),
    retry: false,
    onSuccess: refresh,
  });
}

export function useDeleteWeight(): UseMutationResult<void, ApiError, string> {
  const refresh = useRefresh();
  return useMutation<void, ApiError, string>({
    mutationFn: deleteWeight,
    retry: false,
    onSuccess: refresh,
  });
}
