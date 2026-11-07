import { readFileSync } from "node:fs";
import { join } from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { capture, init, register } = vi.hoisted(() => ({
  capture: vi.fn(),
  init: vi.fn(),
  register: vi.fn(),
}));
vi.mock("posthog-js", () => ({ default: { capture, init, register } }));

import {
  ALLOWED_EVENTS,
  beforeSend,
  filterProps,
  initAnalytics,
  track,
} from "@/lib/analytics";
import { scrubSentryEvent } from "@/lib/sentry-scrub";
import { sanitizeUrl } from "@/lib/url-sanitize";

// Mirrors ALLOWED_EVENTS in apps/api/app/integrations/posthog.py exactly.
const API_ALLOWED_EVENTS = {
  app_opened: [],
  scan_started: ["method"],
  scan_completed: ["found", "method"],
  verdicts_shown: ["member_count"],
  meal_logged: [],
  meal_queued: [],
  meal_log_undone: [],
  meal_removed: [],
  share_result: [],
  share_weekly: [],
  compare_opened: [],
  compare_viewed: [],
  product_search: [],
  diary_entry_added: ["method"],
  diary_day_viewed: [],
  voice_asked: ["language"],
  report_submitted: ["reason"],
  share_clicked: ["kind"],
  account_deleted: [],
};

describe("analytics allow-list", () => {
  beforeEach(() => {
    capture.mockClear();
    init.mockClear();
  });

  it("mirrors the API's ALLOWED_EVENTS exactly", () => {
    expect(
      Object.fromEntries(
        Object.entries(ALLOWED_EVENTS).map(([e, p]) => [e, [...p].sort()]),
      ),
    ).toEqual(API_ALLOWED_EVENTS);
  });

  it("the API file still lists the same events (drift guard)", () => {
    const py = readFileSync(
      join(process.cwd(), "../api/app/integrations/posthog.py"),
      "utf8",
    );
    const block = py.slice(py.indexOf("ALLOWED_EVENTS"), py.indexOf("_ENUMS"));
    const events = [...block.matchAll(/"([a-z_]+)":/g)].map((m) => m[1]);
    expect(events.sort()).toEqual(Object.keys(API_ALLOWED_EVENTS).sort());
  });

  it("track drops unknown props", () => {
    expect(
      filterProps("scan_completed", {
        method: "barcode",
        found: true,
        reason: "allergen_contains",
        conditions: ["diabetes"],
      }),
    ).toEqual({ method: "barcode", found: true });
    expect(filterProps("app_opened", { screen: "home" })).toEqual({});
  });

  it("constrains values: enums, a bool, a bounded count", () => {
    expect(filterProps("scan_started", { method: "label" })).toEqual({
      method: "label",
    });
    expect(filterProps("scan_started", { method: "camera" })).toEqual({});
    expect(filterProps("voice_asked", { language: "fr" })).toEqual({});
    expect(filterProps("report_submitted", { reason: "wrong_values" })).toEqual(
      { reason: "wrong_values" },
    );
    expect(
      filterProps("report_submitted", { reason: "Sugar is wrong" }),
    ).toEqual({});
    expect(filterProps("scan_completed", { found: "yes" })).toEqual({});
    expect(filterProps("verdicts_shown", { member_count: 3 })).toEqual({
      member_count: 3,
    });
    for (const bad of [true, -1, 1001, 2.5, "3"])
      expect(filterProps("verdicts_shown", { member_count: bad })).toEqual({});
    expect(filterProps("share_clicked", { kind: "whatsapp" })).toEqual({
      kind: "whatsapp",
    });
  });

  it("track is a no-op without a key", () => {
    track("app_opened");
    expect(capture).not.toHaveBeenCalled();
    expect(initAnalytics(undefined)).toBe(false);
    expect(init).not.toHaveBeenCalled();
  });

  it("track ignores unknown events and forwards only allowed props once initialised", () => {
    expect(initAnalytics("phc_test")).toBe(true);
    track("label_scan_started");
    track("viewed", { screen: "home" });
    expect(capture).not.toHaveBeenCalled();
    track("scan_completed", {
      method: "barcode",
      found: true,
      allergen: "egg",
    });
    expect(capture).toHaveBeenCalledWith("scan_completed", {
      method: "barcode",
      found: true,
    });
    const cfg = init.mock.calls[0][1];
    expect(cfg.autocapture).toBe(false);
    expect(cfg.capture_pageview).toBe(false);
    expect(cfg.person_profiles).toBe("identified_only");
    expect(cfg.disable_session_recording).toBe(true);
    expect(cfg.disable_surveys).toBe(true);
    expect(cfg.mask_personal_data_properties).toBe(true);
    expect(register).toHaveBeenCalledWith({ $geoip_disable: true });
  });

  it("strips query strings and hashes from urls", () => {
    expect(
      sanitizeUrl("https://x.in/en/sign-in?next=%2Fen%2Fmembers&error=a#h"),
    ).toBe("https://x.in/en/sign-in");
  });
});

describe("posthog beforeSend", () => {
  it("drops any event the allow-list doesn't name (pageviews, autocapture)", () => {
    expect(beforeSend({ event: "$pageview", properties: {} })).toBeNull();
    expect(beforeSend({ event: "$autocapture", properties: {} })).toBeNull();
    expect(
      beforeSend({ event: "label_scan_started", properties: {} }),
    ).toBeNull();
  });

  it("drops non-allowed custom props that reach it", () => {
    const out = beforeSend({
      event: "scan_completed",
      properties: { method: "label", found: true, conditions: ["diabetes"] },
    });
    expect(out?.properties).toEqual({ method: "label", found: true });
  });

  it("sanitizes PostHog's url props and $set, drops titles and other custom props", () => {
    const out = beforeSend({
      event: "app_opened",
      properties: {
        $current_url: "https://x.in/en/a?next=1#h",
        $referrer: "https://g.com/?q=diabetes",
        some_url: "https://x.in/b?c=1",
        title: "Rahul diabetes",
        $title: "Rahul diabetes",
        $set: { $initial_referrer: "https://g.com/?q=x" },
        $set_once: { $initial_current_url: "https://x.in/?e=1" },
      },
    });
    expect(out?.properties).toEqual({
      $current_url: "https://x.in/en/a",
      $referrer: "https://g.com/",
      $set: { $initial_referrer: "https://g.com/" },
      $set_once: { $initial_current_url: "https://x.in/" },
    });
  });
});

describe("scrubSentryEvent exceptions", () => {
  it("redacts exception values, logentry, breadcrumbs", () => {
    const out = scrubSentryEvent({
      exception: {
        values: [{ type: "E", value: "[parameters: {'conditions': ['d']}]" }],
      },
      logentry: { message: "m", params: ["d"] },
      breadcrumbs: [{ message: "d" }],
      extra: { a: "d" },
    });
    expect(JSON.stringify(out)).not.toContain("conditions");
    expect(out.exception.values[0].type).toBe("E");
    expect(out.exception.values[0].value).toBe("<redacted>");
    expect(out).not.toHaveProperty("logentry");
    expect(out).not.toHaveProperty("breadcrumbs");
  });
});

describe("scrubSentryEvent", () => {
  it("removes body, cookies, auth header, query and user pii", () => {
    const out = scrubSentryEvent({
      request: {
        url: "https://x.in/a?next=1",
        data: { a: 1 },
        cookies: { s: "1" },
        query_string: "next=1",
        headers: { Authorization: "Bearer x", Cookie: "c", Accept: "*/*" },
      },
      user: { id: "u", email: "a@b.c", ip_address: "1.1.1.1" },
    });
    expect(out.request).toEqual({
      url: "https://x.in/a",
      headers: { Accept: "*/*" },
    });
    expect(out.user).toEqual({ id: "u" });
  });
});
