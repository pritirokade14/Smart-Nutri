import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

const BASE =
  "inline-flex cursor-pointer select-none items-center justify-center gap-2 rounded-full font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary disabled:cursor-not-allowed disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50";

const VARIANT: Record<ButtonVariant, string> = {
  primary: "bg-brand-primary text-brand-on shadow-sm hover:bg-brand-strong",
  secondary: "bg-brand-soft text-brand-primary hover:bg-surface-muted",
  outline:
    "border border-border-default bg-surface-default text-text-primary hover:bg-surface-muted",
  ghost: "text-text-primary hover:bg-surface-muted",
};

// min-h-11 / min-h-12 keep tap targets at least 44px.
const SIZE: Record<ButtonSize, string> = {
  sm: "min-h-9 px-3 text-sm",
  md: "min-h-11 px-5 text-md",
  lg: "min-h-12 px-6 text-md",
};

export type ButtonStyle = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Full width. */
  block?: boolean;
  className?: string;
};

/** Button classes, for links and labels that should look like a button. */
export function buttonClass({
  variant = "primary",
  size = "md",
  block = false,
  className,
}: ButtonStyle = {}): string {
  return cn(BASE, VARIANT[variant], SIZE[size], block && "w-full", className);
}

export function Button({
  variant,
  size,
  block,
  className,
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & ButtonStyle) {
  return (
    <button
      type={type}
      className={buttonClass({ variant, size, block, className })}
      {...props}
    />
  );
}
