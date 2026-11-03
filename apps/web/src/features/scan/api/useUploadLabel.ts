import { type UseMutationResult, useMutation } from "@tanstack/react-query";
import { getApi } from "@/lib/api/client";
import { ApiError, networkError, toApiError } from "@/lib/api/errors";
import type { ScanDraftOut } from "../lib/draftSchema";
import { resizeImage } from "../lib/resizeImage";

export type UploadStage = "uploading" | "reading";
export type UploadLabelInput = { file: File; barcode?: string };

/**
 * Photo → JPEG (≤ 2000 px, ≤ 8 MB) → signed upload URL → PUT → extraction.
 * Throws ApiError with the API's code (or a client-side one from the resize).
 */
export async function uploadLabel(
  { file, barcode }: UploadLabelInput,
  onStage?: (stage: UploadStage) => void,
): Promise<ScanDraftOut> {
  onStage?.("uploading");
  const jpeg = await resizeImage(file);
  const api = getApi();

  const signed = await api
    .POST("/v1/scans/upload-url", { body: { ext: "jpg" } })
    .catch(() => {
      throw networkError();
    });
  if (signed.error !== undefined || !signed.data) {
    throw toApiError(signed.error, signed.response.status);
  }

  // Straight to Supabase Storage: the signed URL carries its own token, so this
  // request must NOT carry the API bearer token (plain fetch, not the client).
  const put = await fetch(signed.data.upload_url, {
    method: "PUT",
    headers: { "Content-Type": "image/jpeg" },
    body: jpeg,
  }).catch(() => {
    throw networkError();
  });
  if (!put.ok) throw new ApiError("storage_unavailable", put.status);

  onStage?.("reading");
  const scan = await api
    .POST("/v1/scans/label", {
      body: barcode
        ? { path: signed.data.path, barcode }
        : { path: signed.data.path },
    })
    .catch(() => {
      throw networkError();
    });
  if (scan.error !== undefined || !scan.data) {
    throw toApiError(scan.error, scan.response.status);
  }
  return scan.data;
}

export function useUploadLabel(opts?: {
  onStage?: (stage: UploadStage) => void;
}): UseMutationResult<ScanDraftOut, ApiError, UploadLabelInput> {
  return useMutation<ScanDraftOut, ApiError, UploadLabelInput>({
    mutationFn: (input) => uploadLabel(input, opts?.onStage),
    retry: false,
  });
}
