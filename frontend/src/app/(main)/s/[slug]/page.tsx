import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ServicePolaroidCard,
  isCourseService,
  type PublicService,
} from "@entities/service";
import {
  StudioGallery,
  StudioHeader,
  getStudioDisplayName,
} from "@entities/studio";
import { Header } from "@features/navigation/components";
import { ApiError } from "@shared/api/api-error";
import { fetchStudioPublicBySlug } from "@shared/api/server";

import { EmptyServicesState } from "./empty-services-state";

interface StudioStorefrontPageProps {
  params: Promise<{ slug: string }>;
}

async function loadPublicStudio(slug: string) {
  try {
    return await fetchStudioPublicBySlug(slug);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}

export async function generateMetadata({
  params,
}: StudioStorefrontPageProps): Promise<Metadata> {
  const { slug } = await params;
  if (!slug?.trim()) {
    return { title: "Studio | ZeeFrame" };
  }

  try {
    const studio = await fetchStudioPublicBySlug(slug);
    const name = getStudioDisplayName(studio);
    const description =
      studio.description?.trim() || `Book classes at ${name} on ZeeFrame.`;

    return {
      title: `${name} | ZeeFrame`,
      description,
    };
  } catch {
    return { title: "Studio | ZeeFrame" };
  }
}

function serviceBookHref(slug: string, service: PublicService): string {
  return `/s/${encodeURIComponent(slug)}/book/${service.id}`;
}

export default async function StudioStorefrontPage({
  params,
}: StudioStorefrontPageProps) {
  const { slug: rawSlug } = await params;
  const slug = rawSlug?.trim();
  if (!slug) {
    notFound();
  }

  const studio = await loadPublicStudio(slug);
  const services = studio.services ?? [];
  const singleServices = services.filter((service) => !isCourseService(service));
  const courseServices = services.filter((service) => isCourseService(service));
  const orderedServices = [...singleServices, ...courseServices];

  return (
    <>
      <Header
        minimalSearch={{
          href: "/studios",
          placeholder: "Search studios…",
        }}
      />

      <div
        className="mx-auto max-w-3xl px-4 pt-28 pb-16 sm:px-6"
        data-testid="studio-storefront"
      >
        <nav
          className="mb-6 flex items-center gap-1.5 text-xs text-neutral-500"
          aria-label="Breadcrumb"
        >
          <Link
            href="/studios"
            className="transition-colors hover:text-neutral-800"
          >
            Studios
          </Link>
          <span aria-hidden>/</span>
          <span className="truncate font-medium text-neutral-900">
            {getStudioDisplayName(studio)}
          </span>
        </nav>

        <StudioGallery studio={studio} className="mb-6" />
        <StudioHeader studio={studio} className="mb-10" />

        <section aria-labelledby="studio-services-heading">
          <div className="mb-4 flex items-baseline justify-between gap-3">
            <h2
              id="studio-services-heading"
              className="font-display text-xl font-semibold text-neutral-900"
            >
              Classes
            </h2>
            {orderedServices.length > 0 ? (
              <p className="text-xs text-neutral-500">
                {orderedServices.length} published
              </p>
            ) : null}
          </div>

          {orderedServices.length === 0 ? (
            <EmptyServicesState />
          ) : (
            <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {orderedServices.map((service) => (
                <li key={service.id}>
                  <ServicePolaroidCard
                    service={service}
                    href={serviceBookHref(slug, service)}
                  />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  );
}
