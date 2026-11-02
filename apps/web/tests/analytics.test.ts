import { beforeEach, describe, expect, it, vi } from "vitest";

const { capture, init } = vi.hoisted(() => ({
  capture: vi.fn(),
  init: vi.fn(),
}));
vi.mock("posthog-js", () => ({ default: { capture, init } }));

import {
  ALLOWED_EVENT_PROPS,
  filterProps,
  initAnalytics,
  sanitizeUrl,
  track,
} from "@/lib/analytics";
import { scrubSentryEvent } from "@/lib/sentry-scrub";

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
  });

  it("strips query strings and hashes from urls", () => {
    expect(
      sanitizeUrl("https://x.in/en/sign-in?next=%2Fen%2Fmembers&error=a#h"),
    ).toBe("https://x.in/en/sign-in");
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
