import {
  type UseMutationResult,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  type ConsentPurpose,
  type ConsentState,
  consentsKey,
  isGranted,
  recordConsent,
} from "@/features/members/api/members";
import type { ApiError } from "@/lib/api/errors";

export type { ConsentPurpose, ConsentState };
export { isGranted };

/** True when the purpose was granted at an older text version (ask again). */
export function needsUpdate(
  states: readonly ConsentState[] | undefined,
  purpose: ConsentPurpose,
): boolean {
  return Boolean(states?.find((c) => c.purpose === purpose)?.needs_update);
}

export type GrantInput = {
  states: readonly ConsentState[];
  /** Recorded in order; the first one failing stops the rest. */
  required: readonly ConsentPurpose[];
  /** Recorded after the required ones; a failure here is ignored. */
  optional?: readonly ConsentPurpose[];
};

/**
 * Grants purposes at their current text version (from GET /v1/consents) and
 * stores the final states once, so the consent gate re-renders a single time.
 */
export async function grantConsents({
  states,
  required,
  optional = [],
}: GrantInput): Promise<ConsentState[]> {
  const version = (p: ConsentPurpose) =>
    states.find((c) => c.purpose === p)?.current_version;
  let latest = [...states];
  for (const purpose of required) {
    const v = version(purpose);
    if (!v) continue;
    latest = await recordConsent({ purpose, version: v, granted: true });
  }
  for (const purpose of optional) {
    const v = version(purpose);
    if (!v) continue;
    latest = await recordConsent({ purpose, version: v, granted: true }).catch(
      () => latest,
    );
  }
  return latest;
}

export function useGrantConsents(): UseMutationResult<
  ConsentState[],
  ApiError,
  GrantInput
> {
  const client = useQueryClient();
  return useMutation<ConsentState[], ApiError, GrantInput>({
    mutationFn: grantConsents,
    retry: false,
    onSuccess: (states) => client.setQueryData(consentsKey, states),
    // Reload what the server has (an earlier grant may have gone through, or
    // the text changed under us: consent_version_mismatch) and ask again.
    onError: () => void client.invalidateQueries({ queryKey: consentsKey }),
  });
}
