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
      className="flex flex-col items-center justify-center py-24 px-6 text-center"
    >
      <div className="w-12 h-px bg-zinc-200 mb-8" aria-hidden />
      <p className="text-2xl md:text-3xl font-serif italic font-light text-zinc-700 tracking-tight max-w-lg">
        The vibe you&apos;re looking for is currently off the radar.
      </p>
      <p className="text-zinc-500 mt-4 text-sm max-w-md">
        Try another city or category, or clear filters to see all studios.
      </p>
      <Button variant="secondary" className="mt-8" onClick={onReset}>
        Clear filters
      </Button>
    </motion.div>
  );
}
