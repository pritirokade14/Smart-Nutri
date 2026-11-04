import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  getUserTypes,
  putUserTypes,
  setActiveType,
  type UserType,
  type UserTypesIn,
  type UserTypesOut,
  userTypesKey,
} from "../api/userTypes";

// Presentation only (the type never changes a verdict), but it hints at
// health interests: not kept long once nobody is looking at it.
const PERSONAL = { gcTime: 5 * 60_000, retry: false } as const;

export function useUserTypes(): UseQueryResult<UserTypesOut, ApiError> {
  return useQuery<UserTypesOut, ApiError>({
    queryKey: userTypesKey,
    queryFn: getUserTypes,
    ...PERSONAL,
  });
}

/** Saves the types and follow-ups; the response (with `prefill`) is cached. */
export function usePutUserTypes(): UseMutationResult<
  UserTypesOut,
  ApiError,
  UserTypesIn
> {
  const client = useQueryClient();
  return useMutation<UserTypesOut, ApiError, UserTypesIn>({
    mutationFn: putUserTypes,
    retry: false,
    onSuccess: (out) => client.setQueryData(userTypesKey, out),
  });
}

/**
 * Switches the focused mode optimistically and rolls back on error, so the
 * tabs change at once (same as Android's mode switcher).
 */
export function useSetActiveType(): UseMutationResult<
  UserTypesOut,
  ApiError,
  UserType,
  { previous?: UserTypesOut }
> {
  const client = useQueryClient();
  return useMutation<
    UserTypesOut,
    ApiError,
    UserType,
    { previous?: UserTypesOut }
  >({
    mutationFn: setActiveType,
    retry: false,
    onMutate: async (next) => {
      await client.cancelQueries({ queryKey: userTypesKey });
      const previous = client.getQueryData<UserTypesOut>(userTypesKey);
      if (previous)
        client.setQueryData<UserTypesOut>(userTypesKey, {
          ...previous,
          active_type: next,
        });
      return { previous };
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.previous) client.setQueryData(userTypesKey, ctx.previous);
    },
    onSuccess: (out) => client.setQueryData(userTypesKey, out),
  });
}
