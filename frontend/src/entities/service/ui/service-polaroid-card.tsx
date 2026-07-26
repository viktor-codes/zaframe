import Image from "next/image";
import Link from "next/link";
import {
  getPublicServicePriceCents,
  isCourseService,
} from "../model/service";
import type { PublicService } from "../model/types";

export interface ServicePolaroidCardProps {
  service: PublicService;
  /** When set, the whole card links to the booking entry point. */
  href?: string;
  className?: string;
}

function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-EU", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

function serviceTypeLabel(service: PublicService): string {
  return isCourseService(service) ? "Course" : "Drop-in";
}

function serviceMetaLine(service: PublicService): string {
  if (isCourseService(service)) {
    const count = service.occurrences_count;
    const sessions =
      count === 1 ? "1 session" : `${Math.max(count, 0)} sessions`;
    return sessions;
  }

  return `${service.duration_minutes} min`;
}

export function ServicePolaroidCard({
  service,
  href,
  className = "",
}: ServicePolaroidCardProps) {
  const priceCents = getPublicServicePriceCents(service);
  const coverUrl = service.cover_image_url?.trim() || null;
  const typeLabel = serviceTypeLabel(service);
  const meta = serviceMetaLine(service);
  const description = service.description?.trim() || null;

  const body = (
    <>
      <div className="relative aspect-4/5 overflow-hidden rounded-xl bg-neutral-100">
        {coverUrl ? (
          <Image
            src={coverUrl}
            alt={service.name}
            fill
            className="object-cover transition-transform duration-500 group-hover:scale-105"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
            unoptimized={coverUrl.startsWith("http")}
          />
        ) : (
          <div
            className="absolute inset-0 bg-linear-to-br from-sky-100 via-teal-50 to-lime-100"
            aria-hidden
          />
        )}

        <div className="absolute inset-x-3 top-3 flex justify-between gap-2">
          <span className="rounded-lg bg-white/90 px-2.5 py-1 text-[10px] font-bold tracking-widest text-neutral-600 uppercase backdrop-blur-sm">
            {typeLabel}
          </span>
          {isCourseService(service) &&
          service.availability?.requires_warning ? (
            <span className="rounded-lg bg-amber-400 px-2.5 py-1 text-[10px] font-black tracking-wide text-neutral-900 uppercase">
              Limited spots
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-4 px-1">
        <h3 className="truncate font-display text-lg font-bold text-neutral-900">
          {service.name}
        </h3>
        <p className="mt-1 text-xs text-neutral-500">{meta}</p>
        {description ? (
          <p className="mt-2 line-clamp-2 text-sm text-neutral-600">
            {description}
          </p>
        ) : null}
        <div className="mt-3 flex items-end justify-between border-t border-neutral-100 pt-3">
          <span className="font-mono text-lg font-bold text-teal-600">
            {formatPrice(priceCents)}
          </span>
          <span className="font-mono text-[10px] tracking-wide text-neutral-400 uppercase">
            {isCourseService(service) ? "Full course" : "Per session"}
          </span>
        </div>
      </div>
    </>
  );

  const shellClassName = `group block overflow-hidden rounded-2xl bg-white p-3 shadow-paper transition-all duration-300 hover:-translate-y-1 hover:shadow-hover ${className}`;

  if (href) {
    return (
      <Link
        href={href}
        className={shellClassName}
        data-testid="service-polaroid-card"
      >
        <article>{body}</article>
      </Link>
    );
  }

  return (
    <article className={shellClassName} data-testid="service-polaroid-card">
      {body}
    </article>
  );
}
