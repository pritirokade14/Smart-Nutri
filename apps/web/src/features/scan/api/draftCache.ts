import {
  type QueryClient,
  type UseQueryResult,
  useQuery,
} from "@tanstack/react-query";
import { ApiError } from "@/lib/api/errors";
import type { ScanDraftOut } from "../lib/draftSchema";

/**
 * An unconfirmed label draft, handed from the upload page to the confirm page
 * in memory only (there is no GET for a scan). A reload loses it, and the
 * confirm page then offers Retake / Enter manually.
 */
export type CachedDraft = { scan: ScanDraftOut; barcode: string | null };

const KEY = "scan-draft";
const keyFor = (scanId: string) => [KEY, scanId] as const;
// Long enough to finish checking a pack, short enough not to linger.
const DRAFT_GC_MS = 30 * 60 * 1000;

export function setScanDraft(
  client: QueryClient,
  scan: ScanDraftOut,
  barcode: string | null,
): void {
  client.setQueryData<CachedDraft>(keyFor(scan.scan_id), { scan, barcode });
}

export function getScanDraft(
  client: QueryClient,
  scanId: string,
): CachedDraft | undefined {
  return client.getQueryData<CachedDraft>(keyFor(scanId));
}

export function removeScanDraft(client: QueryClient, scanId: string): void {
  client.removeQueries({ queryKey: keyFor(scanId) });
}

/** Drops every draft (label content) on sign-out. */
export function clearScanDrafts(client: QueryClient): void {
  client.removeQueries({ queryKey: [KEY] });
}

/** The draft for this scan, or ApiError scan_not_found if it isn't in memory. */
export function useScanDraft(
  scanId: string | null,
): UseQueryResult<CachedDraft, ApiError> {
  return useQuery<CachedDraft, ApiError>({
    queryKey: keyFor(scanId ?? ""),
    queryFn: () => Promise.reject(new ApiError("scan_not_found", 404)),
    enabled: scanId !== null,
    retry: false,
    gcTime: DRAFT_GC_MS,
    staleTime: Number.POSITIVE_INFINITY,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });
}
