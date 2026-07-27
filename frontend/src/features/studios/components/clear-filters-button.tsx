"use client";

import { Button } from "@shared/ui/button";

export interface ClearFiltersButtonProps {
  onReset: () => void;
}

export function ClearFiltersButton({ onReset }: ClearFiltersButtonProps) {
  return (
    <Button variant="secondary" className="mt-8" onClick={onReset}>
      Clear filters
    </Button>
  );
}
