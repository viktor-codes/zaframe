"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card, Button, Skeleton } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { fetchStudios } from "@/lib/api";

export default function DashboardPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="font-display font-bold text-3xl text-secondary mb-2">
          Dashboard
        </h1>
        <p className="text-neutral-600 mb-8">
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
    queryFn: () =>
      fetchStudios({ owner_id: user!.id, limit: 50 }),
    enabled: !!user?.id,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <Skeleton className="h-6 w-48 mb-2" />
            <Skeleton className="h-4 w-64" />
          </Card>
        ))}
      </div>
    );
  }

  if (!studios || studios.length === 0) {
    return (
      <Card className="p-12 text-center">
        <p className="font-medium text-neutral-700 mb-2">
          You don&apos;t have any studios yet
        </p>
        <p className="text-sm text-neutral-600 mb-6">
          Create your first studio to start accepting bookings.
        </p>
        <Button asChild>
          <Link href="/dashboard/studios/new">Create studio</Link>
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="font-semibold text-secondary text-lg">My studios</h2>
        <Button asChild>
          <Link href="/dashboard/studios/new">Add studio</Link>
        </Button>
      </div>
      <div className="grid gap-4">
        {studios.map((studio) => (
          <Link key={studio.id} href={`/dashboard/studios/${studio.id}`}>
            <Card variant="interactive">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-secondary">{studio.name}</h3>
                  {studio.description && (
                    <p className="text-sm text-neutral-600 mt-1 line-clamp-2">
                      {studio.description}
                    </p>
                  )}
                  <p className="text-xs text-neutral-500 mt-2">
                    {studio.is_active ? (
                      <span className="text-green-600">Active</span>
                    ) : (
                      <span className="text-neutral-500">Inactive</span>
                    )}
                  </p>
                </div>
                <span className="text-primary text-sm font-medium">
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
