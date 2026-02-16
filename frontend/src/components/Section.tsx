"use client";

import { useEffect, useRef } from "react";
import { useInView } from "framer-motion";
import { useUIStore, type HeaderVariant } from "@/store/useUIStore";
import { HEADER_HEIGHT_PX } from "@/lib/constants/layout";
import { cn } from "@/lib/utils";

export interface SectionProps {
  id: string;
  variant: HeaderVariant;
  children: React.ReactNode;
  className?: string;
  /** Отступ сверху при скролле по якорю. По умолчанию — высота хедера. */
  scrollMarginTop?: string | number;
  /** Роль для a11y */
  ariaLabel?: string;
}

export function Section({
  id,
  variant,
  children,
  className,
  scrollMarginTop = HEADER_HEIGHT_PX,
  ariaLabel,
}: SectionProps) {
  const setHeaderVariant = useUIStore((state) => state.setHeaderVariant);
  const ref = useRef<HTMLElement>(null);

  const marginTop =
    typeof scrollMarginTop === "number"
      ? `${scrollMarginTop}px`
      : scrollMarginTop;

  const isInView = useInView(ref, {
    margin: "-10% 0px -70% 0px",
  });

  useEffect(() => {
    if (isInView) {
      setHeaderVariant(variant);
    }
  }, [isInView, variant, setHeaderVariant]);

  return (
    <section
      id={id}
      ref={ref}
      className={cn("relative", className)}
      style={{ scrollMarginTop: marginTop }}
      aria-label={ariaLabel}
    >
      {children}
    </section>
  );
}
