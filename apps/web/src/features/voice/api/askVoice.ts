import type { components } from "@smartnutri/api-client";
import { getApi } from "@/lib/api/client";
import { type ApiError, networkError, toApiError } from "@/lib/api/errors";

export type VoiceAnswer = components["schemas"]["VoiceAnswer"];
export type VoiceLanguage = components["schemas"]["VoiceLanguage"];
type VoiceBody = components["schemas"]["Body_voice_ask"];

export type AskVoiceArgs = {
  audio: Blob;
  memberId: string;
  language: VoiceLanguage;
} & (
  | { productId: string; barcode?: never }
  | { barcode: string; productId?: never }
);

function fileName(type: string): string {
  if (type.includes("webm")) return "question.webm";
  if (type.includes("ogg")) return "question.ogg";
  if (type.includes("mp4") || type.includes("aac")) return "question.m4a";
  return "question.bin";
}

/**
 * POST /v1/voice/ask (F10) as multipart: the recorded question, the member,
 * the language, and exactly one of product_id (our catalogue) or barcode
 * (Open Food Facts). The server sniffs the audio; the verdict in the answer
 * comes from the rules engine. Can take up to about a minute.
 */
export async function askVoice(args: AskVoiceArgs): Promise<VoiceAnswer> {
  const api = getApi();
  const form = new FormData();
  form.append("audio", args.audio, fileName(args.audio.type));
  form.append("member_id", args.memberId);
  form.append("language", args.language);
  if (args.productId) form.append("product_id", args.productId);
  else if (args.barcode) form.append("barcode", args.barcode);
  const body: VoiceBody = {
    // The generated type names the file part `string` (OpenAPI binary);
    // the serializer below sends the FormData built above instead.
    audio: "",
    member_id: args.memberId,
    language: args.language,
  };
  const result = await api
    .POST("/v1/voice/ask", { body, bodySerializer: () => form })
    .catch(() => {
      throw networkError();
    });
  if (result.error !== undefined || !result.data) {
    throw toApiError(result.error, result.response.status);
  }
  return result.data;
}

/**
 * The message for a failed question, or null when another screen takes over
 * (consent_required: the consent prompt asks for ai_processing).
 */
export function voiceErrorKey(error: ApiError): string | null {
  switch (error.code) {
    case "consent_required":
      return null;
    case "rate_limited_voice":
      return "voice.rate_limited";
    case "audio_too_long":
    case "audio_too_large":
      return "voice.too_long";
    case "voice_not_understood":
      return "voice.not_understood";
    case "ai_unavailable":
      return "voice.ai_unavailable";
    default:
      return `error.${error.code}`;
  }
}
