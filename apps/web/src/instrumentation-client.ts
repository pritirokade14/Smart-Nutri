import * as Sentry from "@sentry/nextjs";
import { initAnalytics } from "./lib/analytics";
import { SENTRY_DATA_COLLECTION, scrubSentryEvent } from "./lib/sentry-scrub";

// NEXT_PUBLIC_SENTRY_DSN is not secret (a DSN only allows sending events).
const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
if (dsn) {
  Sentry.init({
    dsn,
    dataCollection: { ...SENTRY_DATA_COLLECTION, httpBodies: [] },
    maxBreadcrumbs: 0,
    tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 0,
    // No Replay integration: never record the screen of a health app.
    integrations: [],
    beforeSend: (event) => scrubSentryEvent(event),
  });
}

initAnalytics(process.env.NEXT_PUBLIC_POSTHOG_KEY);

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
