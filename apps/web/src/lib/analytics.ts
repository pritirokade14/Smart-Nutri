import posthog from "posthog-js";

// Same allow-list as the API (observability.py) and Android (analytics.dart).
export const ALLOWED_EVENT_PROPS: ReadonlySet<string> = new Set([
  "platform",
  "locale",
  "screen",
  "status_code",
  "source",
]);

// Hard-coded ingest host (US cloud). Covered by the CSP's https://*.posthog.com.
export const POSTHOG_HOST = "https://us.i.posthog.com";

export type EventProps = Record<string, unknown>;

export function filterProps(props?: EventProps): EventProps {
  const out: EventProps = {};
  for (const [k, v] of Object.entries(props ?? {})) {
    if (ALLOWED_EVENT_PROPS.has(k)) out[k] = v;
  }
  return out;
}

/** Drops the query string and hash: `?next=` and `?error=` must never leave the browser. */
export function sanitizeUrl(url: string): string {
  try {
    const u = new URL(url);
    return `${u.origin}${u.pathname}`;
  } catch {
    return url.split(/[?#]/)[0];
  }
}

const URL_PROPS = [
  "$current_url",
  "$referrer",
  "$initial_referrer",
  "$initial_current_url",
  "$session_entry_url",
  "$prev_pageview_pathname",
];

type CaptureResult = { properties?: Record<string, unknown> } | null;

function beforeSend<T extends CaptureResult>(event: T): T {
  if (event?.properties) {
    for (const key of URL_PROPS) {
      const v = event.properties[key];
      if (typeof v === "string") event.properties[key] = sanitizeUrl(v);
    }
  }
  return event;
}

let ready = false;

/** Returns false (and does nothing) when there is no key, e.g. CI and tests. */
export function initAnalytics(key: string | undefined): boolean {
  if (!key || ready) return ready;
  posthog.init(key, {
    api_host: POSTHOG_HOST,
    person_profiles: "identified_only",
    autocapture: false,
    capture_pageview: true,
    capture_pageleave: false,
    // No scripts loaded at runtime (keeps strict-dynamic CSP simple), no recording.
    disable_session_recording: true,
    disable_surveys: true,
    disable_conversations: true,
    disable_external_dependency_loading: true,
    capture_heatmaps: false,
    capture_dead_clicks: false,
    capture_exceptions: false,
    advanced_disable_flags: true,
    before_send: beforeSend,
  });
  ready = true;
  return true;
}

export function track(event: string, props?: EventProps): void {
  if (!ready) return;
  posthog.capture(event, filterProps(props));
}
