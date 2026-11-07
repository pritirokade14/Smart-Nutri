import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { mealsKey } from "@/features/meals/api/meals";
import type { ApiError } from "@/lib/api/errors";
import {
  addFavourite,
  addFavouriteMeal,
  deleteFavourite,
  type FavouriteIn,
  type FavouriteLogIn,
  type FavouriteLogOut,
  type FavouriteMealIn,
  type FavouriteOut,
  type FavouritesOut,
  favouritesKey,
  listFavourites,
  logFavourite,
} from "../api/favourites";

const PERSONAL = { gcTime: 60_000, retry: false } as const;

export function useFavourites(
  enabled = true,
): UseQueryResult<FavouritesOut, ApiError> {
  return useQuery<FavouritesOut, ApiError>({
    queryKey: favouritesKey,
    queryFn: listFavourites,
    enabled,
    ...PERSONAL,
  });
}

// Every write refreshes everything under ["meals"]: the list, the recents
// (their favourite_id) and the diary. Never retried automatically.
function useWrite<V, R>(
  fn: (v: V) => Promise<R>,
): UseMutationResult<R, ApiError, V> {
  const client = useQueryClient();
  return useMutation<R, ApiError, V>({
    mutationFn: fn,
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: mealsKey }),
  });
}

export const useAddFavourite = (): UseMutationResult<
  FavouriteOut,
  ApiError,
  FavouriteIn
> => useWrite(addFavourite);

export const useAddFavouriteMeal = (): UseMutationResult<
  FavouriteOut,
  ApiError,
  FavouriteMealIn
> => useWrite(addFavouriteMeal);

export const useDeleteFavourite = (): UseMutationResult<
  void,
  ApiError,
  string
> => useWrite(deleteFavourite);

export const useLogFavourite = (): UseMutationResult<
  FavouriteLogOut,
  ApiError,
  { id: string; body: FavouriteLogIn }
> => useWrite(({ id, body }) => logFavourite(id, body));
