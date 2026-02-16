import { create } from "zustand";

export type HeaderVariant = "on-light" | "on-dark";

interface UIState {
  headerVariant: HeaderVariant;
  setHeaderVariant: (variant: HeaderVariant) => void;
}

export const useUIStore = create<UIState>((set) => ({
  headerVariant: "on-light",
  setHeaderVariant: (variant) => set({ headerVariant: variant }),
}));
