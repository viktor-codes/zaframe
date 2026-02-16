"use client";

import { cn } from "@/lib/utils";

type SectionHeadingSize = "hero" | "section" | "subsection" | "label";

const sizeStyles: Record<
  SectionHeadingSize,
  { className: string; defaultTag: "h1" | "h2" | "h3" | "span" }
> = {
  hero: {
    className:
      "text-[clamp(4rem,8vw,5.5rem)] font-bold tracking-tight leading-[1.1] text-balance",
    defaultTag: "h1",
  },
  section: {
    className:
      "text-[clamp(3rem,4vw+1rem,5rem)] font-bold tracking-tighter leading-[1.1] text-balance",
    defaultTag: "h2",
  },
  subsection: {
    className:
      "text-[clamp(1.25rem,2vw+0.5rem,1.75rem)] font-semibold tracking-tight text-balance",
    defaultTag: "h3",
  },
  label: {
    className: "text-[10px] font-black uppercase tracking-[0.4em]",
    defaultTag: "span",
  },
};

export interface SectionHeadingProps {
  size?: SectionHeadingSize;
  as?: "h1" | "h2" | "h3" | "span";
  children: React.ReactNode;
  className?: string;
}

export function SectionHeading({
  size = "section",
  as,
  children,
  className,
}: SectionHeadingProps) {
  const config = sizeStyles[size];
  const Tag = as ?? config.defaultTag;

  return <Tag className={cn(config.className, className)}>{children}</Tag>;
}
