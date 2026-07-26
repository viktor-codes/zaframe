import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { isCourseService } from "@entities/service";
import { getStudioDisplayName } from "@entities/studio";
import { BookOccurrenceWizard } from "@features/book-occurrence";
import { Header } from "@features/navigation/components";
import { ApiError } from "@shared/api/api-error";
import { fetchStudioPublicBySlug } from "@shared/api/server";
import { Button } from "@shared/ui";

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

function CourseCheckoutUnavailable({
  slug,
  studioName,
  serviceName,
}: {
  slug: string;
  studioName: string;
  serviceName: string;
}) {
  return (
    <div
      className="mx-auto max-w-lg px-4 pt-28 pb-16 text-center sm:px-6"
      data-testid="course-checkout-unavailable"
    >
      <h1 className="font-display text-2xl font-bold text-neutral-900">
        Course booking is coming soon
      </h1>
      <p className="mt-3 text-sm text-neutral-600">
        {serviceName} at {studioName} is a full course. Drop-in checkout is not
        available for courses yet — browse other classes on the studio page.
      </p>
      <div className="mt-8">
        <Button asChild>
          <Link href={`/s/${encodeURIComponent(slug)}`}>Back to studio</Link>
        </Button>
      </div>
    </div>
  );
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
      {isCourseService(service) ? (
        <CourseCheckoutUnavailable
          slug={slug}
          studioName={getStudioDisplayName(studio)}
          serviceName={service.name}
        />
      ) : (
        <BookOccurrenceWizard
          slug={slug}
          studioId={studio.id}
          studioName={getStudioDisplayName(studio)}
          service={service}
        />
      )}
    </>
  );
}
