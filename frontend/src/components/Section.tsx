"use client";

import {
  createContext,
  useContext,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import { useInView } from "framer-motion";
import { useUIStore, type HeaderVariant } from "@/store/useUIStore";
import { HEADER_HEIGHT_PX } from "@/lib/constants/layout";
import { cn } from "@/lib/utils";

/** Состояние видимости контента секции для CSS-анимаций (Intersection Observer). */
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
