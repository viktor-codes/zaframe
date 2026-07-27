"use client";

import { cn } from "@shared/lib/utils";

import { SectionHeading, type SectionHeadingProps } from "./section-heading";
import { useSectionInView } from "./section";

const transitionClasses = "transition-all duration-500 ease-out";
const inViewClasses = "opacity-100 translate-y-0";
const notInViewClasses = "opacity-0 translate-y-4";

export interface AnimatedSectionHeadingProps extends SectionHeadingProps {
  /** Disable the reveal animation (enabled by default inside Section). */
  animate?: boolean;
}

/**
 * SectionHeading with IntersectionObserver reveal via Section context.
 * Use only where the fade-in is needed — prefer plain SectionHeading in RSC.
 */
export function AnimatedSectionHeading({
  animate = true,
  className,
  ...props
}: AnimatedSectionHeadingProps) {
  const sectionView = useSectionInView();
  const shouldAnimate = animate && sectionView !== null;
  const visible = shouldAnimate ? sectionView.inView : true;

  return (
    <SectionHeading
      {...props}
      className={cn(
        className,
        shouldAnimate && transitionClasses,
        shouldAnimate && (visible ? inViewClasses : notInViewClasses),
      )}
    />
  );
}
