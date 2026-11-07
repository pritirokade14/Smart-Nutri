/**
 * The Diary's add-food context (the web twin of Android's
 * diaryAddContextProvider). Search, barcode and label open as separate pages,
 * so the context lives in sessionStorage (this tab only, never sent anywhere).
 * It holds the day, the slot and the method only: no product, member or
 * health data. LogMealDialog reads it, and clears it after a log.
 */
const KEY = "sn.diaryAddContext";

export type DiaryAddMethod = "search" | "barcode" | "label";

export type DiaryAddContext = {
  method: DiaryAddMethod;
  /** The chosen slot; null: the server's suggestion. */
  slotId: string | null;
  /** A past day (YYYY-MM-DD); null for today. */
  localDate: string | null;
};

const METHODS: readonly string[] = ["search", "barcode", "label"];

/** An unfinished add-food trip older than this no longer applies. */
export const ADD_CONTEXT_TTL_MS = 30 * 60 * 1000;

/** Pages of the add-food trip (after the locale); leaving them drops the context. */
const TRIP = /^\/[^/]+\/(diary|search|scan|result|product)(\/|$)/;

export function isAddTripPath(pathname: string): boolean {
  return TRIP.test(pathname);
}

export function setDiaryAddContext(ctx: DiaryAddContext): void {
  try {
    window.sessionStorage.setItem(
      KEY,
      JSON.stringify({ ...ctx, at: Date.now() }),
    );
  } catch {
    // Storage may be blocked: the log then goes to now, as before.
  }
}

export function clearDiaryAddContext(): void {
  try {
    window.sessionStorage.removeItem(KEY);
  } catch {
    // Nothing to clear.
  }
}

export function getDiaryAddContext(): DiaryAddContext | null {
  try {
    const raw = window.sessionStorage.getItem(KEY);
    if (!raw) return null;
    const v = JSON.parse(raw) as Partial<DiaryAddContext> & { at?: number };
    if (typeof v.at !== "number" || Date.now() - v.at > ADD_CONTEXT_TTL_MS) {
      window.sessionStorage.removeItem(KEY);
      return null;
    }
    if (typeof v.method !== "string" || !METHODS.includes(v.method))
      return null;
    return {
      method: v.method as DiaryAddMethod,
      slotId: typeof v.slotId === "string" ? v.slotId : null,
      localDate:
        typeof v.localDate === "string" &&
        /^\d{4}-\d{2}-\d{2}$/.test(v.localDate)
          ? v.localDate
          : null,
    };
  } catch {
    return null;
  }
}
