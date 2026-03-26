"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { motion } from "framer-motion";
import { Heart, Check } from "lucide-react";
import type { SearchResult } from "@/types/search";

const PLACEHOLDER_IMAGE =
  "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?auto=format&fit=crop&q=80&w=800";

function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-EU", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

function categoryLabel(category: string): string {
  const labels: Record<string, string> = {
    yoga: "Yoga",
    boxing: "Boxing",
    dance: "Dance",
    hiit: "HIIT",
    pilates: "Pilates",
    martial_arts: "Martial Arts",
    strength: "Strength",
  };
  return labels[category] ?? category;
}

function studioTypeLabel(services: SearchResult["matched_services"]): string {
  const first = services[0];
  return first ? categoryLabel(first.category) : "Studio";
}

function mockRating(studioId: number): string {
  return (4 + (studioId % 10) / 10).toFixed(1);
}

export interface StudioSearchCardProps {
  result: SearchResult;
  index?: number;
}

const cardStagger = 0.05;
const cardDuration = 0.35;

export function StudioSearchCard({ result, index = 0 }: StudioSearchCardProps) {
  const [saved, setSaved] = useState(false);
  const { studio, matched_services } = result;
  const imageUrl = studio.cover_image_url ?? PLACEHOLDER_IMAGE;
  const priceCandidates = (matched_services ?? []).map((s) => {
    const cents =
      s.price_course_cents != null && s.price_course_cents > 0
        ? s.price_course_cents
        : s.price_single_cents;
    return typeof cents === "number" && Number.isFinite(cents) ? cents : null;
  });
  const validPrices = priceCandidates.filter((c): c is number => c != null);
  const minPrice = validPrices.length > 0 ? Math.min(...validPrices) : null;
  const showSpotsLeft = studio.id % 5 === 0;
  const typeLabel = studioTypeLabel(matched_services);
  const rating = mockRating(studio.id);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: cardDuration,
        delay: index * cardStagger,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
    >
      <article className="group overflow-hidden rounded-2xl bg-white p-3 shadow-lg transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:shadow-teal-500/10">
        <div className="relative aspect-9/10 overflow-hidden rounded-xl bg-zinc-100">
          <Image
            src={imageUrl}
            alt={studio.name}
            fill
            className="object-cover transition-transform duration-500 group-hover:scale-110"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
            unoptimized={imageUrl.startsWith("http")}
          />

          <div className="absolute inset-x-3 top-3 flex items-start justify-between">
            <div className="flex items-center gap-1 rounded-full bg-teal-500 px-2.5 py-1 text-[10px] font-bold text-white uppercase shadow-lg">
              <Check className="h-3 w-3" strokeWidth={3} />
              Verified
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setSaved((prev) => !prev);
              }}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-white/90 backdrop-blur-sm transition-all hover:scale-110"
              aria-label={saved ? "Unsave" : "Save"}
            >
              <Heart
                className={`h-4 w-4 ${saved ? "fill-red-500 text-red-500" : "text-zinc-400"}`}
                strokeWidth={2}
              />
            </button>
          </div>

          <div className="absolute inset-x-3 bottom-3 flex items-end justify-between">
            {showSpotsLeft && (
              <div className="rounded-lg bg-amber-400 px-2.5 py-1 text-[10px] font-black tracking-wide text-zinc-900 uppercase">
                🔥 5 spots left
              </div>
            )}
            {!showSpotsLeft && <div />}
            <div className="rounded-lg bg-white/90 px-2.5 py-1 text-[10px] font-bold tracking-widest text-zinc-600 uppercase backdrop-blur-sm">
              {typeLabel}
            </div>
          </div>
        </div>

        <div className="mt-4 px-1">
          <h3 className="mb-1 truncate text-xl font-bold text-zinc-900">
            {studio.name}
          </h3>
          <div className="mb-3 flex items-center gap-2 text-xs text-zinc-500">
            <span className="flex items-center gap-0.5">
              <span className="text-amber-400">⭐</span> {rating}
            </span>
            <span>•</span>
            <span>📍 {studio.city ?? "—"}</span>
          </div>
          <div className="flex items-center justify-between border-t border-zinc-100 pt-3">
            <div className="font-mono text-lg font-bold text-teal-600">
              {minPrice != null ? formatPrice(minPrice) : "—"}
            </div>
            <div className="font-mono text-[10px] text-zinc-400 uppercase">
              From session
            </div>
          </div>
          <Link
            href={`/studios/${studio.id}`}
            className="mt-4 flex w-full items-center justify-center rounded-xl bg-zinc-900 py-3 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
          >
            View Details
          </Link>
        </div>
      </article>
    </motion.div>
  );
}
