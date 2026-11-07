/**
 * The portion preview (G14): quantity x grams_per_unit x per_100 / 100,
 * rounded half-up to one decimal place. The only arithmetic on the web, done
 * on exact decimals (BigInt mantissa and scale from String(n)) so 1.15 never
 * becomes 1.1. A missing value stays null: never 0.
 */

type Dec = { m: bigint; s: number };

function parse(n: number): Dec {
  const text = String(n).toLowerCase();
  const [mant, exp = "0"] = text.split("e");
  const [intPart, frac = ""] = mant.replace("-", "").split(".");
  const sign = mant.startsWith("-") ? -1n : 1n;
  let m = sign * BigInt(intPart + frac);
  let s = frac.length - Number(exp);
  if (s < 0) {
    m *= 10n ** BigInt(-s);
    s = 0;
  }
  return { m, s };
}

function toOneDp(m: bigint, s: number): string {
  // value = m / 10^s; round half-up (away from zero) to 1 dp.
  const neg = m < 0n;
  const abs = neg ? -m : m;
  let tenths: bigint;
  if (s <= 1) tenths = abs * 10n ** BigInt(1 - s);
  else {
    const div = 10n ** BigInt(s - 1);
    tenths = (abs + div / 2n) / div;
  }
  const text = tenths.toString().padStart(2, "0");
  const out = `${text.slice(0, -1)}.${text.slice(-1)}`;
  return neg && tenths !== 0n ? `-${out}` : out;
}

export function previewValue(
  per100: number | null | undefined,
  quantity: number,
  gramsPerUnit: number,
): string | null {
  if (per100 == null) return null;
  const a = parse(per100);
  const q = parse(quantity);
  const g = parse(gramsPerUnit);
  // per100 x quantity x grams / 100
  return toOneDp(a.m * q.m * g.m, a.s + q.s + g.s + 2);
}

export function previewPortion(
  per100: Readonly<Record<string, number | null | undefined>>,
  quantity: number,
  gramsPerUnit: number,
): Record<string, string | null> {
  return Object.fromEntries(
    Object.entries(per100).map(([k, v]) => [
      k,
      previewValue(v, quantity, gramsPerUnit),
    ]),
  );
}
