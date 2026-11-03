"""Load sanity check for the SmartNutri API (Plan 8 Task 7).

    uv run --with httpx python scripts/load_smoke.py \\
        --base-url http://localhost:8000 --rps 20 --seconds 60 --barcode 8901063012345

Sends a fixed request rate, alternating between `GET /v1/health` and
`GET /v1/products/{barcode}/public`. Both are unauthenticated and free: the script never calls
a CallMissed-backed or authenticated route, and never sends a token.

Prints p50, p95 and max latency (ms) per endpoint and overall, plus counts by status.
Exits 1 if:
- the overall p95 is over `--p95-ms` (default 800);
- any response is a 5xx;
- any request failed at the transport level.

`429` responses do not fail the run. The public route has a per-IP limit
(`RATE_LIMIT_PUBLIC_PER_MINUTE`, default 60), so a single machine at 20 rps will see 429s on
it. They are reported. Raise the limit on the target for the test, or read the health numbers.
The barcode must be one the target can serve (seeded, or cached from Open Food Facts):
- a cache miss calls Open Food Facts;
- a 404 counts as a normal response.
"""

from __future__ import annotations

import argparse
import asyncio
import math
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass

import httpx

USER_AGENT = "SmartNutri-load-smoke/1.0"


@dataclass(frozen=True)
class Sample:
    endpoint: str
    status: int | None  # None = transport error or timeout
    ms: float


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile (pct in 0..100). Empty input -> 0."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]


async def _one(client: httpx.AsyncClient, endpoint: str, path: str) -> Sample:
    start = time.perf_counter()
    try:
        response = await client.get(path)
        status: int | None = response.status_code
    except httpx.HTTPError:
        status = None
    return Sample(endpoint, status, (time.perf_counter() - start) * 1000)


async def run(
    base_url: str, rps: float, seconds: float, barcode: str, timeout: float
) -> list[Sample]:
    targets = [("health", "/v1/health"), ("public_product", f"/v1/products/{barcode}/public")]
    total = max(1, int(rps * seconds))
    limits = httpx.Limits(max_connections=200, max_keepalive_connections=50)
    async with httpx.AsyncClient(
        base_url=base_url.rstrip("/"),
        timeout=timeout,
        limits=limits,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        tasks: list[asyncio.Task[Sample]] = []
        for i in range(total):
            # Fixed schedule (open model): request i starts at t0 + i/rps, however slow the
            # server is, so latency is measured honestly under the target rate.
            delay = t0 + i / rps - loop.time()
            if delay > 0:
                await asyncio.sleep(delay)
            endpoint, path = targets[i % len(targets)]
            tasks.append(asyncio.create_task(_one(client, endpoint, path)))
        return list(await asyncio.gather(*tasks))


def report(samples: list[Sample], p95_limit: float) -> int:
    by_endpoint: dict[str, list[Sample]] = defaultdict(list)
    for s in samples:
        by_endpoint[s.endpoint].append(s)

    def line(name: str, group: list[Sample]) -> str:
        ms = [s.ms for s in group if s.status is not None]
        return (
            f"{name:<16} n={len(group):<5} p50={percentile(ms, 50):7.1f}ms "
            f"p95={percentile(ms, 95):7.1f}ms max={max(ms, default=0):7.1f}ms"
        )

    for name in sorted(by_endpoint):
        print(line(name, by_endpoint[name]))
    print(line("overall", samples))

    statuses = Counter("error" if s.status is None else str(s.status) for s in samples)
    print("status counts: " + ", ".join(f"{k}={v}" for k, v in sorted(statuses.items())))

    ok_ms = [s.ms for s in samples if s.status is not None]
    p95 = percentile(ok_ms, 95)
    server_errors = sum(1 for s in samples if s.status is not None and s.status >= 500)
    transport_errors = statuses.get("error", 0)
    rate_limited = statuses.get("429", 0)
    if rate_limited:
        print(
            f"note: {rate_limited} responses were 429 (per-IP public limit); "
            "raise RATE_LIMIT_PUBLIC_PER_MINUTE on the target for a cleaner run"
        )

    failures = []
    if p95 > p95_limit:
        failures.append(f"p95 {p95:.1f}ms > {p95_limit:.0f}ms")
    if server_errors:
        failures.append(f"{server_errors} responses were 5xx")
    if transport_errors:
        failures.append(f"{transport_errors} requests failed (timeout or connection)")
    if failures:
        print("FAIL: " + "; ".join(failures))
        return 1
    print("PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--rps", type=float, default=20)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--barcode", required=True)
    parser.add_argument("--p95-ms", type=float, default=800)
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args(argv)
    if args.rps <= 0 or args.seconds <= 0:
        parser.error("--rps and --seconds must be positive")
    if not args.barcode.isdigit():
        parser.error("--barcode must be digits")
    print(
        f"load smoke: {args.base_url} at {args.rps:g} rps for {args.seconds:g}s "
        f"({int(args.rps * args.seconds)} requests)"
    )
    samples = asyncio.run(run(args.base_url, args.rps, args.seconds, args.barcode, args.timeout))
    return report(samples, args.p95_ms)


if __name__ == "__main__":
    sys.exit(main())
