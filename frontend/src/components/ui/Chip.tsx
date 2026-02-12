"use client";

export type ChipTone = "neutral" | "brand" | "success" | "warning" | "danger";
export type ChipSize = "xs" | "sm" | "md";

export interface ChipProps extends React.HTMLAttributes<HTMLDivElement> {
  tone?: ChipTone;
  size?: ChipSize;
}

const tones: Record<ChipTone, string> = {
  neutral:
    "bg-white/85 text-zinc-900 border border-black/10 dark:bg-zinc-800/85 dark:text-zinc-100 dark:border-white/10",
  brand: "bg-gradient-to-br from-sky-50 to-teal-50 text-zinc-900 border border-teal-200/50",
  success:
    "bg-emerald-50 text-emerald-900 border border-emerald-200",
  warning: "bg-amber-50 text-amber-900 border border-amber-200",
  danger: "bg-red-50 text-red-900 border border-red-200",
};

const sizeClasses: Record<ChipSize, string> = {
  xs: "px-2 py-0.5 text-[10px]",
  sm: "px-3 py-1 text-xs",
  md: "px-4 py-1.5 text-sm",
};

export function Chip({
  tone = "neutral",
  size = "sm",
  className = "",
  children,
  ...props
}: ChipProps) {
  return (
    <div
      className={`inline-flex items-center rounded-full font-semibold backdrop-blur ${tones[tone]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
