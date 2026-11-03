import posthog from "posthog-js";
import { sanitizeUrl } from "./url-sanitize";

// Mirrors ALLOWED_EVENTS in apps/api/app/integrations/posthog.py exactly
// (and Android's analytics.dart): only these events, only these props. Never
// conditions, allergens, diet, reasons, per-member statuses, nutrients,
// names, emails or ids. tests/analytics.test.ts checks the API file.
export const ALLOWED_EVENTS: Readonly<Record<string, ReadonlySet<string>>> = {
  app_opened: new Set(),
  scan_started: new Set(["method"]),
  scan_completed: new Set(["method", "found"]),
  verdicts_shown: new Set(["member_count"]),
  meal_logged: new Set(),
  voice_asked: new Set(["language"]),
  report_submitted: new Set(["reason"]),
  share_clicked: new Set(["kind"]),
  account_deleted: new Set(),
};

// Same value rules as the API: closed sets, a bool, a bounded count, else a
// short lowercase token.
const ENUMS: Readonly<Record<string, ReadonlySet<string>>> = {
  method: new Set(["barcode", "label", "manual", "search"]),
  language: new Set(["en", "hi", "mr"]),
  reason: new Set([
    "wrong_values",
    "wrong_ingredients",
    "wrong_product",
    "other",
  ]),
  kind: new Set(["link", "image", "whatsapp"]),
};
const BOOLS = new Set(["found"]);
const COUNTS = new Set(["member_count"]);
const TOKEN = /^[a-z0-9_]{1,40}$/;

// Hard-coded ingest host (US cloud). Covered by the CSP's https://*.posthog.com.
export const POSTHOG_HOST = "https://us.i.posthog.com";

export type EventProps = Record<string, unknown>;

function safe(key: string, v: unknown): boolean {
  if (BOOLS.has(key)) return typeof v === "boolean";
  if (COUNTS.has(key))
    return typeof v === "number" && Number.isInteger(v) && v >= 0 && v <= 1000;
  if (typeof v !== "string" || !TOKEN.test(v)) return false;
  const allowed = ENUMS[key];
  return !allowed || allowed.has(v);
}

/** The event's allowed props with safe values; everything else is dropped. */
export function filterProps(event: string, props?: EventProps): EventProps {
  const allowed = ALLOWED_EVENTS[event];
  const out: EventProps = {};
  if (!allowed) return out;
  for (const [k, v] of Object.entries(props ?? {})) {
    if (allowed.has(k) && safe(k, v)) out[k] = v;
  }
  return out;
}

type PropBag = Record<string, unknown>;
type CaptureResult = { event?: string; properties?: PropBag } | null;

function sanitizeBag(bag: PropBag): void {
  for (const key of Object.keys(bag)) {
    const v = bag[key];
    if (typeof v === "string" && /url|referrer/i.test(key)) {
      bag[key] = sanitizeUrl(v);
    }
  }
}

/**
 * PostHog before_send: drops every event the allow-list doesn't name
 * (pageviews, autocapture, anything a library adds); keeps PostHog's own `$`
 * props with URLs cut to their path; drops titles and any other custom prop.
 */
export function beforeSend<T extends CaptureResult>(event: T): T | null {
  const name = event?.event;
  if (typeof name !== "string" || !ALLOWED_EVENTS[name]) return null;
  const props = event?.properties;
  if (props) {
    const custom = filterProps(name, props);
    for (const key of Object.keys(props)) {
      if (!key.startsWith("$") && !(key in custom)) delete props[key];
    }
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
    // Only allow-listed events: no automatic pageviews.
    capture_pageview: false,
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

/** Sends an allow-listed event; an unknown event is dropped (named in dev). */
export function track(event: string, props?: EventProps): void {
  if (!ALLOWED_EVENTS[event]) {
    if (process.env.NODE_ENV === "development")
      console.warn(`analytics: dropped unknown event ${event}`);
    return;
  }
  if (!ready) return;
  posthog.capture(event, filterProps(event, props));
}
