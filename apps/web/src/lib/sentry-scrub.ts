import { sanitizeUrl } from "./analytics";

type SentryLike = {
  request?: {
    url?: string;
    data?: unknown;
    cookies?: unknown;
    query_string?: unknown;
    headers?: Record<string, string>;
  };
  user?: Record<string, unknown>;
};

const SENSITIVE_HEADERS = new Set(["authorization", "cookie", "x-api-key"]);

/** Sentry beforeSend: strip bodies, cookies, auth headers, query strings and user PII. */
export function scrubSentryEvent<T extends object>(input: T): T {
  const event = input as SentryLike;
  const req = event.request;
  if (req) {
    delete req.data;
    delete req.cookies;
    delete req.query_string;
    if (req.url) req.url = sanitizeUrl(req.url);
    if (req.headers) {
      for (const k of Object.keys(req.headers)) {
        if (SENSITIVE_HEADERS.has(k.toLowerCase())) delete req.headers[k];
      }
    }
  }
  if (event.user) {
    delete event.user.email;
    delete event.user.ip_address;
    delete event.user.username;
  }
  return input;
}

/**
 * @sentry/nextjs 11 replaced `sendDefaultPii` with `dataCollection`. Everything off:
 * no user info, cookies, headers, request/response bodies, query params or local variables.
 */
export const SENTRY_DATA_COLLECTION = {
  userInfo: false,
  cookies: false,
  httpHeaders: false,
  httpBodies: [],
  urlQueryParams: false,
  databaseQueryData: false,
  queues: false,
  stackFrameVariables: false,
} as const;
