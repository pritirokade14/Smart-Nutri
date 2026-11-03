import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  type ConsentIn,
  type ConsentState,
  consentsKey,
  createMember,
  deleteMember,
  getMember,
  listConsents,
  listMembers,
  type MemberIn,
  type MemberOut,
  type MemberPatch,
  memberKey,
  membersKey,
  recordConsent,
  updateMember,
} from "../api/members";

// Health data: never kept long once nobody is looking at it.
const HEALTH = { gcTime: 60_000, retry: false } as const;

export function useMembers(): UseQueryResult<MemberOut[], ApiError> {
  return useQuery<MemberOut[], ApiError>({
    queryKey: membersKey,
    queryFn: listMembers,
    ...HEALTH,
  });
}

export function useMember(id: string): UseQueryResult<MemberOut, ApiError> {
  return useQuery<MemberOut, ApiError>({
    queryKey: memberKey(id),
    queryFn: () => getMember(id),
    ...HEALTH,
  });
}

export type SaveMember =
  | { id?: undefined; body: MemberIn }
  | { id: string; body: MemberPatch };

/** Create (no id) or update (id) a member; refreshes the list on success. */
export function useSaveMember(): UseMutationResult<
  MemberOut,
  ApiError,
  SaveMember
> {
  const client = useQueryClient();
  return useMutation<MemberOut, ApiError, SaveMember>({
    mutationFn: (v) =>
      v.id === undefined ? createMember(v.body) : updateMember(v.id, v.body),
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: membersKey }),
  });
}

export function useDeleteMember(): UseMutationResult<void, ApiError, string> {
  const client = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: deleteMember,
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: membersKey }),
  });
}

export function useConsents(): UseQueryResult<ConsentState[], ApiError> {
  return useQuery<ConsentState[], ApiError>({
    queryKey: consentsKey,
    queryFn: listConsents,
    ...HEALTH,
  });
}

/** Records one consent and stores the returned states (all purposes). */
export function useRecordConsent(): UseMutationResult<
  ConsentState[],
  ApiError,
  ConsentIn
> {
  const client = useQueryClient();
  return useMutation<ConsentState[], ApiError, ConsentIn>({
    mutationFn: recordConsent,
    retry: false,
    onSuccess: (states) => client.setQueryData(consentsKey, states),
  });
}
