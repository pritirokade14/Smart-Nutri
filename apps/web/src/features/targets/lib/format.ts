// Latin digits in every locale (packages/i18n README, rule 4).
const INT = new Intl.NumberFormat("en", { maximumFractionDigits: 0 });
const ONE_DP = new Intl.NumberFormat("en", { maximumFractionDigits: 1 });
const TWO_DP = new Intl.NumberFormat("en", { maximumFractionDigits: 2 });

/** Whole kcal or grams, as the API rounded them ("1,540"). */
export const formatInt = (n: number): string => INT.format(n);
/** Weights, 1 dp. */
export const formatWeight = (n: number): string => ONE_DP.format(n);
/** Rates, factors and g per kg, up to 2 dp. */
export const formatRate = (n: number): string => TWO_DP.format(n);
