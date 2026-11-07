import {
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  archiveMealSlot,
  createMealSlot,
  listMealSlots,
  type MealSlotCreateIn,
  type MealSlotRenameIn,
  type MealSlotsOut,
  mealSlotsKey,
  renameMealSlot,
  reorderMealSlots,
} from "../api/mealSlots";

export function useMealSlots(
  includeArchived = false,
): UseQueryResult<MealSlotsOut, ApiError> {
  return useQuery<MealSlotsOut, ApiError>({
    queryKey: mealSlotsKey(includeArchived),
    queryFn: () => listMealSlots(includeArchived),
    gcTime: 60_000,
    retry: false,
  });
}

/** Slot writes change what Today shows, so every meals query is refreshed. */
function useSlotMutation<V, R>(fn: (v: V) => Promise<R>) {
  const qc = useQueryClient();
  return useMutation<R, ApiError, V>({
    mutationFn: fn,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["meals"] }),
  });
}

export const useCreateMealSlot = () =>
  useSlotMutation((v: MealSlotCreateIn) => createMealSlot(v));
export const useRenameMealSlot = () =>
  useSlotMutation((v: { id: string; body: Partial<MealSlotRenameIn> }) =>
    renameMealSlot(v.id, v.body),
  );
export const useReorderMealSlots = () =>
  useSlotMutation((ids: string[]) => reorderMealSlots(ids));
export const useArchiveMealSlot = () =>
  useSlotMutation((id: string) => archiveMealSlot(id));
