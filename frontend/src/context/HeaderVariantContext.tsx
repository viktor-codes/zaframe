"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

// Используем названия, описывающие состояние хедера, а не тему сайта
type HeaderVariant = "on-light" | "on-dark" | "transparent";

interface HeaderVariantContextType {
  variant: HeaderVariant;
  setVariant: (variant: HeaderVariant) => void;
}

const HeaderVariantContext = createContext<
  HeaderVariantContextType | undefined
>(undefined);

export const HeaderVariantProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const [variant, setVariant] = useState<HeaderVariant>("on-light");

  return (
    <HeaderVariantContext.Provider value={{ variant, setVariant }}>
      {children}
    </HeaderVariantContext.Provider>
  );
};

export const useHeaderVariant = () => {
  const context = useContext(HeaderVariantContext);
  if (!context) {
    throw new Error(
      "useHeaderVariant must be used within a HeaderVariantProvider",
    );
  }
  return context;
};
