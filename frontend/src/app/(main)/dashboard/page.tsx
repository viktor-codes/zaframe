"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card, Button, Skeleton } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { fetchStudios } from "@/lib/api";
import type { StudioResponse } from "@/types/studio";

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
        Dashboard
      </h1>
      <p className="mb-8 text-neutral-600">
        Manage your studios, slots, and bookings.
      </p>
      <MyStudios />
    </div>
  );
}

function MyStudios() {
  const { user } = useAuth();

  const { data: studios, isLoading } = useQuery({
    queryKey: ["studios", "owner", user?.id],
    queryFn: () => fetchStudios({ owner_id: user!.id, limit: 50 }),
    enabled: !!user?.id,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <Skeleton className="mb-2 h-6 w-48" />
            <Skeleton className="h-4 w-64" />
          </Card>
        ))}
      </div>
    );
  }

  if (!studios || studios.length === 0) {
    return (
      <Card className="p-12 text-center">
        <p className="mb-2 font-medium text-neutral-700">
          You don&apos;t have any studios yet
        </p>
        <p className="mb-6 text-sm text-neutral-600">
          Create your first studio to start accepting bookings.
        </p>
        <Button asChild>
          <Link href="/dashboard/studios/new">Create studio</Link>
        </Button>
      </Card>
    );
  }

  const ownerStudios = studios as StudioResponse[];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-secondary text-lg font-semibold">My studios</h2>
        <Button asChild>
          <Link href="/dashboard/studios/new">Add studio</Link>
        </Button>
      </div>
      <div className="grid gap-4">
        {ownerStudios.map((studio) => (
          <Link key={studio.id} href={`/dashboard/studios/${studio.id}`}>
            <Card variant="interactive">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-secondary font-semibold">
                    {studio.name}
                  </h3>
                  {studio.description && (
                    <p className="mt-1 line-clamp-2 text-sm text-neutral-600">
                      {studio.description}
                    </p>
                  )}
                  <p className="mt-2 text-xs text-neutral-500">
                    {studio.is_active ? (
                      <span className="text-green-600">Active</span>
                    ) : (
                      <span className="text-neutral-500">Inactive</span>
                    )}
                  </p>
                </div>
                <span className="text-sm font-medium text-primary">
                  Manage →
                </span>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
