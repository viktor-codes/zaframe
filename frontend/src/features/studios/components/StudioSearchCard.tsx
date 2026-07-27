import Link from "next/link";
import Image from "next/image";
import { Check } from "lucide-react";

import type { SearchResult } from "@entities/studio";
import { formatMoneyFromCents } from "@shared/lib/format-money";

import { SaveStudioButton } from "./save-studio-button";

const PLACEHOLDER_IMAGE =
  "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?auto=format&fit=crop&q=80&w=800";

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
  /** Kept for call-site compatibility; entrance stagger is CSS-free now. */
  index?: number;
}

export function StudioSearchCard({ result }: StudioSearchCardProps) {
  const { studio, matched_services } = result;
  const imageUrl = PLACEHOLDER_IMAGE;
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
          <SaveStudioButton />
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
            {minPrice != null ? formatMoneyFromCents(minPrice) : "—"}
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
  );
}
