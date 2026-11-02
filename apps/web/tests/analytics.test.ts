import { beforeEach, describe, expect, it, vi } from "vitest";

const { capture, init, register } = vi.hoisted(() => ({
  capture: vi.fn(),
  init: vi.fn(),
  register: vi.fn(),
}));
vi.mock("posthog-js", () => ({ default: { capture, init, register } }));

import {
  ALLOWED_EVENT_PROPS,
  beforeSend,
  filterProps,
  initAnalytics,
  track,
} from "@/lib/analytics";
import { scrubSentryEvent } from "@/lib/sentry-scrub";
import { sanitizeUrl } from "@/lib/url-sanitize";

describe("analytics allow-list", () => {
  beforeEach(() => {
    capture.mockClear();
    init.mockClear();
  });

  it("has the shared allow-list", () => {
    expect([...ALLOWED_EVENT_PROPS].sort()).toEqual(
      ["locale", "platform", "screen", "source", "status_code"].sort(),
    );
  });

  it("drops non-allowed keys and keeps allowed ones", () => {
    expect(filterProps({ conditions: ["diabetes"] })).toEqual({});
    expect(filterProps({ screen: "home", allergies: ["x"] })).toEqual({
      screen: "home",
    });
  });

  it("track is a no-op without a key", () => {
    track("viewed", { screen: "home" });
    expect(capture).not.toHaveBeenCalled();
    expect(initAnalytics(undefined)).toBe(false);
    expect(init).not.toHaveBeenCalled();
  });

  it("track forwards only allowed props once initialised", () => {
    expect(initAnalytics("phc_test")).toBe(true);
    track("viewed", { conditions: ["diabetes"], screen: "home" });
    expect(capture).toHaveBeenCalledWith("viewed", { screen: "home" });
    const cfg = init.mock.calls[0][1];
    expect(cfg.autocapture).toBe(false);
    expect(cfg.person_profiles).toBe("identified_only");
    expect(cfg.capture_pageview).toBe(true);
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

describe("allow-listed values are constrained", () => {
  it("accepts valid values", () => {
    const ok = {
      locale: "hi",
      platform: "web",
      screen: "scan_page",
      source: "nav",
      status_code: 404,
    };
    expect(filterProps(ok)).toEqual(ok);
  });
  it("drops invalid values", () => {
    expect(
      filterProps({
        locale: "fr",
        platform: "ios",
        screen: "Diabetes Home",
        source: "a".repeat(41),
        status_code: "200",
      }),
    ).toEqual({});
  });
});

describe("posthog beforeSend", () => {
  it("sanitizes url-like props, $set and drops titles", () => {
    const out = beforeSend({
      event: "$pageview",
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
      some_url: "https://x.in/b",
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
