"use client";

import Link from "next/link";
import Image from "next/image";
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

export interface StudioSearchCardProps {
  result: SearchResult;
}

export function StudioSearchCard({ result }: StudioSearchCardProps) {
  const { studio, matched_services } = result;
  const imageUrl = studio.cover_image_url ?? PLACEHOLDER_IMAGE;
  const minPrice =
    matched_services.length > 0
      ? Math.min(
          ...matched_services.map((s) =>
            s.price_course_cents != null && s.price_course_cents > 0
              ? s.price_course_cents
              : s.price_single_cents
          )
        )
      : null;

  return (
    <Link href={`/studios/${studio.id}`} className="block group">
      <article className="relative w-full rounded-2xl bg-white shadow-md overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:shadow-xl">
        <div className="aspect-video relative w-full overflow-hidden bg-zinc-100">
          <Image
            src={imageUrl}
            alt={studio.name}
            fill
            className="object-cover transition duration-500 group-hover:scale-105"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            unoptimized={imageUrl.startsWith("http")}
          />
        </div>
        <div className="p-4">
          <h2 className="text-lg font-bold tracking-tight text-zinc-900 truncate">
            {studio.name}
          </h2>
          {studio.city && (
            <p className="text-sm text-zinc-500 mt-0.5">{studio.city}</p>
          )}
          {matched_services.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {matched_services.slice(0, 5).map((s) => (
                <span
                  key={s.id}
                  className="inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-700"
                >
                  {categoryLabel(s.category)}
                </span>
              ))}
              {matched_services.length > 5 && (
                <span className="text-xs text-zinc-400">
                  +{matched_services.length - 5}
                </span>
              )}
            </div>
          )}
          {minPrice != null && (
            <p className="mt-3 text-sm font-semibold text-teal-600">
              From {formatPrice(minPrice)}
            </p>
          )}
        </div>
      </article>
    </Link>
  );
}
