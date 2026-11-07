import type { SVGProps } from "react";

// Small stroke icons drawn for SmartNutri (24×24 grid, currentColor). They
// are always decorative: the text next to them carries the meaning.
type IconProps = Omit<SVGProps<SVGSVGElement>, "children">;

function Icon({
  name,
  className,
  children,
  ...rest
}: IconProps & { name: string; children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      data-icon={name}
      className={className ?? "size-5 shrink-0"}
      {...rest}
    >
      {children}
    </svg>
  );
}

export const CheckCircleIcon = (p: IconProps) => (
  <Icon name="check-circle" {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M8 12.5l2.8 2.8L16.5 9" />
  </Icon>
);

export const AlertTriangleIcon = (p: IconProps) => (
  <Icon name="alert-triangle" {...p}>
    <path d="M12 3.5L21.5 20H2.5z" />
    <path d="M12 10v4.5" />
    <path d="M12 17.5h.01" />
  </Icon>
);

export const StopIcon = (p: IconProps) => (
  <Icon name="stop" {...p}>
    <path d="M8 3h8l5 5v8l-5 5H8l-5-5V8z" />
    <path d="M9.5 9.5l5 5M14.5 9.5l-5 5" />
  </Icon>
);

export const QuestionCircleIcon = (p: IconProps) => (
  <Icon name="question-circle" {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M9.6 9.4a2.5 2.5 0 1 1 3.4 2.3c-.6.3-1 .8-1 1.5v.6" />
    <path d="M12 17h.01" />
  </Icon>
);

export const InfoIcon = (p: IconProps) => (
  <Icon name="info" {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5.5" />
    <path d="M12 7.5h.01" />
  </Icon>
);

export const HomeIcon = (p: IconProps) => (
  <Icon name="home" {...p}>
    <path d="M3.5 10.5L12 4l8.5 6.5V20a1 1 0 0 1-1 1H15v-6H9v6H4.5a1 1 0 0 1-1-1z" />
  </Icon>
);

export const ScanIcon = (p: IconProps) => (
  <Icon name="scan" {...p}>
    <path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3" />
    <path d="M8 9v6M11 9v6M14 9v6M16.5 9v6" />
  </Icon>
);

export const HistoryIcon = (p: IconProps) => (
  <Icon name="history" {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3.5 2" />
  </Icon>
);

export const FamilyIcon = (p: IconProps) => (
  <Icon name="family" {...p}>
    <circle cx="9" cy="8" r="3.5" />
    <path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6" />
    <circle cx="17.5" cy="9.5" r="2.5" />
    <path d="M17.5 14.5c2.4 0 4 1.8 4 4.5" />
  </Icon>
);

export const UserIcon = (p: IconProps) => (
  <Icon name="user" {...p}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c0-4.2 3.6-7 8-7s8 2.8 8 7" />
  </Icon>
);

export const CameraIcon = (p: IconProps) => (
  <Icon name="camera" {...p}>
    <path d="M3 8.5A1.5 1.5 0 0 1 4.5 7h2.8L9 4.5h6L16.7 7h2.8A1.5 1.5 0 0 1 21 8.5V18a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18z" />
    <circle cx="12" cy="13" r="3.5" />
  </Icon>
);

export const UploadIcon = (p: IconProps) => (
  <Icon name="upload" {...p}>
    <path d="M12 15V4M7.5 8.5L12 4l4.5 4.5" />
    <path d="M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4" />
  </Icon>
);

export const PencilIcon = (p: IconProps) => (
  <Icon name="pencil" {...p}>
    <path d="M4 20h4L19 9l-4-4L4 16z" />
    <path d="M13.5 6.5l4 4" />
  </Icon>
);

export const ArrowRightIcon = (p: IconProps) => (
  <Icon name="arrow-right" {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Icon>
);

export const RefreshIcon = (p: IconProps) => (
  <Icon name="refresh" {...p}>
    <path d="M20 11a8 8 0 1 0-2.3 5.7" />
    <path d="M20 4v7h-7" />
  </Icon>
);

export const GlobeIcon = (p: IconProps) => (
  <Icon name="globe" {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18" />
    <path d="M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z" />
  </Icon>
);

export const SearchIcon = (p: IconProps) => (
  <Icon name="search" {...p}>
    <circle cx="10.5" cy="10.5" r="6.5" />
    <path d="M15.5 15.5L20 20" />
  </Icon>
);

export const SearchOffIcon = (p: IconProps) => (
  <Icon name="search-off" {...p}>
    <circle cx="10.5" cy="10.5" r="6.5" />
    <path d="M15.5 15.5L20 20" />
    <path d="M8.5 8.5l4 4M12.5 8.5l-4 4" />
  </Icon>
);

/** The SmartNutri mark: a leaf inside a rounded tile. */
export const LeafIcon = (p: IconProps) => (
  <Icon name="leaf" {...p}>
    <path d="M5 19c0-8.3 5.7-14 15-14 0 9.3-5.7 15-14 15" />
    <path d="M5 19l8-8" />
  </Icon>
);

export const CloseIcon = (p: IconProps) => (
  <Icon name="close" {...p}>
    <path d="M6 6l12 12M18 6L6 18" />
  </Icon>
);

export const PlusIcon = (p: IconProps) => (
  <Icon name="plus" {...p}>
    <path d="M12 5v14M5 12h14" />
  </Icon>
);

export const SparkleIcon = (p: IconProps) => (
  <Icon name="sparkle" {...p}>
    <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z" />
    <path d="M19 16v4M17 18h4" />
  </Icon>
);

export const DumbbellIcon = (p: IconProps) => (
  <Icon name="dumbbell" {...p}>
    <path d="M7 7v10M17 7v10M4 9.5v5M20 9.5v5M7 12h10" />
  </Icon>
);

export const CompareIcon = (p: IconProps) => (
  <Icon name="compare" {...p}>
    <rect x="3.5" y="4" width="7" height="16" rx="1.5" />
    <rect x="13.5" y="4" width="7" height="16" rx="1.5" />
  </Icon>
);

export const MoreIcon = (p: IconProps) => (
  <Icon name="more" {...p}>
    <circle cx="6" cy="12" r="1.2" />
    <circle cx="12" cy="12" r="1.2" />
    <circle cx="18" cy="12" r="1.2" />
  </Icon>
);

export const EyeIcon = (p: IconProps) => (
  <Icon name="eye" {...p}>
    <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" />
    <circle cx="12" cy="12" r="3" />
  </Icon>
);

export const EyeOffIcon = (p: IconProps) => (
  <Icon name="eye-off" {...p}>
    <path d="M3 3l18 18" />
    <path d="M10.6 5.1A10.6 10.6 0 0112 5c6.4 0 10 7 10 7a17 17 0 01-3.2 4.1M6.6 6.6A16.6 16.6 0 002 12s3.6 7 10 7a10 10 0 004.4-1" />
    <path d="M9.9 9.9a3 3 0 004.2 4.2" />
  </Icon>
);
