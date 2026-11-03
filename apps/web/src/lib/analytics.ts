import posthog from "posthog-js";
import { sanitizeUrl } from "./url-sanitize";

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

const LOCALES = new Set(["en", "hi", "mr"]);
const PLATFORMS = new Set(["android", "web", "api"]);
const TOKEN = /^[a-z_]{1,40}$/;

function validValue(key: string, v: unknown): boolean {
  switch (key) {
    case "locale":
      return typeof v === "string" && LOCALES.has(v);
    case "platform":
      return typeof v === "string" && PLATFORMS.has(v);
    case "status_code":
      return typeof v === "number" && Number.isInteger(v);
    default:
      return typeof v === "string" && TOKEN.test(v);
  }
}

export function filterProps(props?: EventProps): EventProps {
  const out: EventProps = {};
  for (const [k, v] of Object.entries(props ?? {})) {
    if (ALLOWED_EVENT_PROPS.has(k) && validValue(k, v)) out[k] = v;
  }
  return out;
}

type PropBag = Record<string, unknown>;
type CaptureResult = { properties?: PropBag } | null;

function sanitizeBag(bag: PropBag): void {
  for (const key of Object.keys(bag)) {
    const v = bag[key];
    if (typeof v === "string" && /url|referrer/i.test(key)) {
      bag[key] = sanitizeUrl(v);
    }
  }
}

/** PostHog before_send: no query strings/hashes in URLs, no page titles. */
export function beforeSend<T extends CaptureResult>(event: T): T {
  const props = event?.properties;
  if (props) {
    delete props.title;
    delete props.$title;
    sanitizeBag(props);
    for (const nested of ["$set", "$set_once"]) {
      const bag = props[nested];
      if (bag && typeof bag === "object") sanitizeBag(bag as PropBag);
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
    mask_personal_data_properties: true,
    before_send: beforeSend,
  });
  posthog.register({ $geoip_disable: true });
  ready = true;
  return true;
}

/** Forgets this browser's analytics identity (after account deletion). */
export function resetAnalytics(): void {
  if (ready) posthog.reset();
}

export function track(event: string, props?: EventProps): void {
  if (!ready) return;
  posthog.capture(event, filterProps(props));
}
