"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/Button";

export interface EmptyStateProps {
  onReset: () => void;
}

export function EmptyState({ onReset }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center px-6 py-24 text-center"
    >
      <div className="mb-8 h-px w-12 bg-zinc-200" aria-hidden />
      <p className="max-w-lg font-serif text-2xl font-light tracking-tight text-zinc-700 italic md:text-3xl">
        The vibe you&apos;re looking for is currently off the radar.
      </p>
      <p className="mt-4 max-w-md text-sm text-zinc-500">
        Try another city or category, or clear filters to see all studios.
      </p>
      <Button variant="secondary" className="mt-8" onClick={onReset}>
        Clear filters
      </Button>
    </motion.div>
  );
}
