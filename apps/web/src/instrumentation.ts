import * as Sentry from "@sentry/nextjs";
import { SENTRY_DATA_COLLECTION, scrubSentryEvent } from "./lib/sentry-scrub";

export async function register(): Promise<void> {
  const dsn = process.env.SENTRY_DSN;
  if (!dsn) return;
  Sentry.init({
    dsn,
    dataCollection: { ...SENTRY_DATA_COLLECTION, httpBodies: [] },
    maxBreadcrumbs: 0,
    tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 0,
    beforeSend: (event) => scrubSentryEvent(event),
  });
}

export const onRequestError = Sentry.captureRequestError;
