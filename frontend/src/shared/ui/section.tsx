"use client";

import {
  createContext,
  useContext,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import { useInView } from "framer-motion";
import { cn, useUIStore, type HeaderVariant } from "@shared/lib";

/** Section content visibility state for CSS animations (Intersection Observer). */
interface SectionViewContextValue {
  inView: boolean;
}

const SectionViewContext = createContext<SectionViewContextValue | null>(null);

export function useSectionInView(): SectionViewContextValue | null {
  return useContext(SectionViewContext);
}

export interface SectionProps {
  id: string;
  variant: HeaderVariant;
  children: ReactNode;
  className?: string;
  /** Top offset when scrolling to the anchor. Defaults to the header height. */
  scrollMarginTop?: string | number;
  /** Accessible label for the section landmark. */
  ariaLabel?: string;
}

export function Section({
  id,
  variant,
  children,
  className,
  scrollMarginTop,
  ariaLabel,
}: SectionProps) {
  const setHeaderVariant = useUIStore((state) => state.setHeaderVariant);
  const ref = useRef<HTMLElement>(null);

  const marginTop =
    typeof scrollMarginTop === "number"
      ? `${scrollMarginTop}px`
      : scrollMarginTop;

  const headerInView = useInView(ref, {
    margin: "-10% 0px -70% 0px",
  });

  const contentInView = useInView(ref, {
    amount: 0.2,
    once: true,
  });

  useEffect(() => {
    if (headerInView) {
      setHeaderVariant(variant);
    }
  }, [headerInView, variant, setHeaderVariant]);

  return (
    <section
      id={id}
      ref={ref}
      className={cn("relative", className)}
      style={{ scrollMarginTop: marginTop }}
      aria-label={ariaLabel}
    >
      <SectionViewContext.Provider value={{ inView: contentInView }}>
        {children}
      </SectionViewContext.Provider>
    </section>
  );
}
