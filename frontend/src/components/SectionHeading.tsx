"use client";

import { useSectionInView } from "@/components/Section";
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

const transitionClasses =
  "transition-all duration-500 ease-out";
const inViewClasses = "opacity-100 translate-y-0";
const notInViewClasses = "opacity-0 translate-y-4";

export interface SectionHeadingProps {
  size?: SectionHeadingSize;
  as?: "h1" | "h2" | "h3" | "span";
  children: React.ReactNode;
  className?: string;
  /** Отключить анимацию появления (по умолчанию включена внутри Section). */
  animate?: boolean;
}

export function SectionHeading({
  size = "section",
  as,
  children,
  className,
  animate = true,
}: SectionHeadingProps) {
  const config = sizeStyles[size];
  const Tag = as ?? config.defaultTag;
  const sectionView = useSectionInView();

  const shouldAnimate = animate && sectionView !== null;
  const visible = shouldAnimate ? sectionView!.inView : true;

  return (
    <Tag
      className={cn(
        config.className,
        className,
        shouldAnimate && transitionClasses,
        shouldAnimate && (visible ? inViewClasses : notInViewClasses),
      )}
    >
      {children}
    </Tag>
  );
}
