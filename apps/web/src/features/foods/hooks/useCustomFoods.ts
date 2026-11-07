import {
  type InfiniteData,
  type UseInfiniteQueryResult,
  type UseMutationResult,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  type CustomFoodIn,
  type CustomFoodOut,
  type CustomFoodsOut,
  createCustomFood,
  customFoodsKey,
  deleteCustomFood,
  listCustomFoods,
  updateCustomFood,
} from "../api/customFoods";

const PERSONAL = { gcTime: 60_000, retry: false } as const;

export function useCustomFoods(): UseInfiniteQueryResult<
  InfiniteData<CustomFoodsOut>,
  ApiError
> {
  return useInfiniteQuery<
    CustomFoodsOut,
    ApiError,
    InfiniteData<CustomFoodsOut>,
    readonly string[],
    string | null
  >({
    queryKey: customFoodsKey,
    queryFn: ({ pageParam }) => listCustomFoods(pageParam),
    initialPageParam: null,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
    ...PERSONAL,
  });
}

/** The API has no single-food read: the edit form finds it in the list pages. */
export function useCustomFoodById(id: string) {
  const q = useCustomFoods();
  const items = q.data?.pages.flatMap((p) => p.items) ?? [];
  const found: CustomFoodOut | undefined = items.find((f) => f.id === id);
  return { ...q, food: found };
}

export function useSaveCustomFood(
  id?: string,
): UseMutationResult<CustomFoodOut, ApiError, CustomFoodIn> {
  const client = useQueryClient();
  return useMutation<CustomFoodOut, ApiError, CustomFoodIn>({
    mutationFn: (body) =>
      id ? updateCustomFood(id, body) : createCustomFood(body),
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: ["meals"] }),
  });
}

export function useDeleteCustomFood(): UseMutationResult<
  void,
  ApiError,
  string
> {
  const client = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: deleteCustomFood,
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: ["meals"] }),
  });
}
