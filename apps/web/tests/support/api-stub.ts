import type { vi } from "vitest";

// A tiny router over the stubbed global fetch: the real getApi() and the
// generated client send Requests; each test answers by method + path.

export type Call = {
  method: string;
  path: string;
  body: unknown;
  query: URLSearchParams;
};
type Handler = (call: Call, n: number) => Response | Promise<Response>;

export const json = (status: number, body?: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

export const envelope = (code: string, details: object = {}) => ({
  error: { code, message_key: `error.${code}`, details },
});

export function apiStub(fetchMock: ReturnType<typeof vi.fn>) {
  const routes = new Map<string, Handler>();
  const calls: Call[] = [];
  const counts = new Map<string, number>();
  fetchMock.mockImplementation(async (input: Request) => {
    const url = new URL(input.url);
    const text = await input.clone().text();
    const call: Call = {
      method: input.method,
      path: url.pathname,
      body: text ? JSON.parse(text) : undefined,
      query: url.searchParams,
    };
    calls.push(call);
    const key = `${call.method} ${call.path}`;
    const n = (counts.get(key) ?? 0) + 1;
    counts.set(key, n);
    const handler = routes.get(key);
    if (!handler) return json(404, envelope("not_found"));
    return handler(call, n);
  });
  return {
    on(method: string, path: string, handler: Handler | Response | object) {
      routes.set(
        `${method} ${path}`,
        typeof handler === "function"
          ? (handler as Handler)
          : handler instanceof Response
            ? () => handler.clone()
            : () => json(200, handler),
      );
      return this;
    },
    calls,
    callsTo(method: string, path: string) {
      return calls.filter((c) => c.method === method && c.path === path);
    },
  };
}

export const consentStates = (granted: {
  health_data?: boolean;
  ai_processing?: boolean;
}) =>
  (["terms", "health_data", "ai_processing"] as const).map((purpose) => ({
    purpose,
    granted: Boolean(granted[purpose as keyof typeof granted]),
    version: granted[purpose as keyof typeof granted] ? "2026-11-01" : null,
    current_version: "2026-11-01",
  }));
