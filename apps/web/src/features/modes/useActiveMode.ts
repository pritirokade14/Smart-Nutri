import { useUserTypes } from "@/features/user-types/hooks/useUserTypes";
import { byPriority, DEFAULT_TYPE, type UserType } from "./layouts";

// The last mode seen in this tab, so an error or a refetch never flips the
// bar back to the default (Android caches it in memory the same way).
let lastMode: UserType | undefined;

/**
 * The focused mode: the API's resolved `active_type`, else the last one
 * seen, else `eat_better` (loading, offline, error). Presentation only: the
 * mode never reaches the result screen, a verdict or an allergy check.
 */
export function useActiveMode(): { mode: UserType; types: UserType[] } {
  const { data } = useUserTypes();
  if (data) lastMode = data.active_type;
  return {
    mode: data?.active_type ?? lastMode ?? DEFAULT_TYPE,
    types: byPriority(data?.types ?? []),
  };
}

/** Test hook: forget the cached mode. */
export function resetActiveModeCache(): void {
  lastMode = undefined;
}
