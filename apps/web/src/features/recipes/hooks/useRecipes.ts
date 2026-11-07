import {
  type InfiniteData,
  type UseInfiniteQueryResult,
  type UseMutationResult,
  type UseQueryResult,
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  createRecipe,
  deleteRecipe,
  getRecipe,
  listRecipes,
  type RecipeIn,
  type RecipeOut,
  type RecipesOut,
  recipeKey,
  recipesKey,
  updateRecipe,
} from "../api/recipes";

const PERSONAL = { gcTime: 60_000, retry: false } as const;

export function useRecipes(): UseInfiniteQueryResult<
  InfiniteData<RecipesOut>,
  ApiError
> {
  return useInfiniteQuery<
    RecipesOut,
    ApiError,
    InfiniteData<RecipesOut>,
    readonly string[],
    string | null
  >({
    queryKey: recipesKey,
    queryFn: ({ pageParam }) => listRecipes(pageParam),
    initialPageParam: null,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
    ...PERSONAL,
  });
}

export function useRecipe(id: string): UseQueryResult<RecipeOut, ApiError> {
  return useQuery<RecipeOut, ApiError>({
    queryKey: recipeKey(id),
    queryFn: () => getRecipe(id),
    ...PERSONAL,
  });
}

export function useSaveRecipe(
  id?: string,
): UseMutationResult<RecipeOut, ApiError, RecipeIn> {
  const client = useQueryClient();
  return useMutation<RecipeOut, ApiError, RecipeIn>({
    mutationFn: (body) => (id ? updateRecipe(id, body) : createRecipe(body)),
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: ["meals"] }),
  });
}

export function useDeleteRecipe(): UseMutationResult<void, ApiError, string> {
  const client = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: deleteRecipe,
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: ["meals"] }),
  });
}
