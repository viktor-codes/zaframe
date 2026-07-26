import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getStudioDisplayName } from "@entities/studio";
import { BookOccurrenceWizard } from "@features/book-occurrence";
import { Header } from "@features/navigation/components";
import { ApiError } from "@shared/api/api-error";
import { fetchStudioPublicBySlug } from "@shared/api/server";

interface BookServicePageProps {
  params: Promise<{ slug: string; serviceId: string }>;
}

async function loadStudio(slug: string) {
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
}: BookServicePageProps): Promise<Metadata> {
  const { slug, serviceId } = await params;
  try {
    const studio = await loadStudio(slug);
    const service = studio.services?.find((item) => item.id === Number(serviceId));
    const studioName = getStudioDisplayName(studio);
    return {
      title: service
        ? `Book ${service.name} · ${studioName} | ZeeFrame`
        : `Book · ${studioName} | ZeeFrame`,
    };
  } catch {
    return { title: "Book class | ZeeFrame" };
  }
}

export default async function BookServicePage({ params }: BookServicePageProps) {
  const { slug: rawSlug, serviceId: rawServiceId } = await params;
  const slug = rawSlug?.trim();
  const serviceId = Number(rawServiceId);

  if (!slug || !Number.isInteger(serviceId) || serviceId <= 0) {
    notFound();
  }

  const studio = await loadStudio(slug);
  const service = studio.services?.find((item) => item.id === serviceId);
  if (!service) {
    notFound();
  }

  return (
    <>
      <Header
        minimalSearch={{
          href: "/studios",
          placeholder: "Search studios…",
        }}
      />
      <BookOccurrenceWizard
        slug={slug}
        studioId={studio.id}
        studioName={getStudioDisplayName(studio)}
        service={service}
      />
    </>
  );
}
