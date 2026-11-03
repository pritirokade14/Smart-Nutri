import {
  AlertTriangleIcon,
  CheckCircleIcon,
  QuestionCircleIcon,
  StopIcon,
} from "./icons";

export type VerdictStatus = "ok" | "caution" | "unknown" | "avoid";

const KNOWN = new Set<string>(["ok", "caution", "unknown", "avoid"]);

/**
 * The status exactly as the API sent it; anything unexpected is "unknown"
 * (grey), never "ok". This only guards rendering; it never decides a verdict.
 */
export function toneOf(status: string | null | undefined): VerdictStatus {
  return status && KNOWN.has(status) ? (status as VerdictStatus) : "unknown";
}

/**
 * A distinct shape per status, so the status never relies on colour alone.
 * The colour comes from CSS keyed on the nearest data-verdict attribute
 * (globals.css), whose default is the unknown grey.
 */
export function VerdictIcon({
  status,
  className,
}: {
  status: VerdictStatus;
  className?: string;
}) {
  switch (status) {
    case "ok":
      return <CheckCircleIcon className={className} />;
    case "caution":
      return <AlertTriangleIcon className={className} />;
    case "avoid":
      return <StopIcon className={className} />;
    default:
      return <QuestionCircleIcon className={className} />;
  }
}
