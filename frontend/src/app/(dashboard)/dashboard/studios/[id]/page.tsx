"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { RequireStudioRole } from "@shared/auth";
import { queryKeys, StudioMemberRole } from "@shared/lib";
import { Card, Button, Input, Textarea, Skeleton } from "@shared/ui";
import {
  createOccurrence,
  deleteOccurrence,
  fetchOccurrenceBookings,
  fetchStudio,
  fetchStudioOccurrences,
  fetchStudioServices,
  updateStudio,
} from "@shared/api";
import type { OccurrenceResponse } from "@entities/occurrence";

function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function StudioManagePage() {
  const params = useParams();
  const id = Number(params.id);

  if (Number.isNaN(id)) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          Invalid studio
        </div>
      </div>
    );
  }

  return (
    <RequireStudioRole
      studioId={id}
      roles={[StudioMemberRole.OWNER, StudioMemberRole.MANAGER]}
    >
      <StudioManageContent studioId={id} />
    </RequireStudioRole>
  );
}

function StudioManageContent({ studioId }: { studioId: number }) {
  const queryClient = useQueryClient();
  const id = studioId;
  const occurrenceFilters = useMemo(() => ({ size: 100 }), []);

  const [editMode, setEditMode] = useState(false);
  const [showAddOccurrence, setShowAddOccurrence] = useState(false);

  const { data: studio, isLoading } = useQuery({
    queryKey: queryKeys.studio.detail(id),
    queryFn: () => fetchStudio(id),
  });

  const { data: occurrences } = useQuery({
    queryKey: queryKeys.studio.occurrences(id, occurrenceFilters),
    queryFn: () => fetchStudioOccurrences(id, occurrenceFilters),
    enabled: !!studio,
  });

  if (isLoading || !studio) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-12">
        <Skeleton className="mb-6 h-8 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <Link
        href="/dashboard"
        className="mb-6 inline-block text-sm font-medium text-primary hover:text-primary-dark"
      >
        ← Back to dashboard
      </Link>

      <StudioEditForm
        studio={studio}
        editMode={editMode}
        onEditModeChange={setEditMode}
        onSuccess={() =>
          queryClient.invalidateQueries({ queryKey: queryKeys.studio.detail(id) })
        }
      />

      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-secondary font-display text-xl font-semibold">
            Sessions (schedule)
          </h2>
          <Button onClick={() => setShowAddOccurrence((v) => !v)}>
            {showAddOccurrence ? "Cancel" : "Add session"}
          </Button>
        </div>

        {showAddOccurrence && (
          <OccurrenceCreateForm
            studioId={id}
            onSuccess={() => {
              queryClient.invalidateQueries({
                queryKey: queryKeys.studio.occurrences(id, occurrenceFilters),
              });
              setShowAddOccurrence(false);
            }}
            onCancel={() => setShowAddOccurrence(false)}
          />
        )}

        <div className="mt-4 space-y-4">
          {occurrences?.length === 0 ? (
            <Card className="p-8 text-center text-neutral-600">
              No sessions yet. Add a session to accept bookings.
            </Card>
          ) : (
            occurrences?.map((occurrence) => (
              <OccurrenceCard
                key={occurrence.id}
                occurrence={occurrence}
                onDeleted={() =>
                  queryClient.invalidateQueries({
                    queryKey: queryKeys.studio.occurrences(id, occurrenceFilters),
                  })
                }
              />
            ))
          )}
        </div>
      </section>
    </div>
  );
}

function StudioEditForm({
  studio,
  editMode,
  onEditModeChange,
  onSuccess,
}: {
  studio: {
    id: number;
    name: string;
    description?: string | null;
    email?: string | null;
    phone?: string | null;
    address?: string | null;
    is_active: boolean;
  };
  editMode: boolean;
  onEditModeChange: (v: boolean) => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState({
    name: studio.name,
    description: studio.description ?? "",
    email: studio.email ?? "",
    phone: studio.phone ?? "",
    address: studio.address ?? "",
    is_active: studio.is_active,
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (data: typeof form) =>
      updateStudio(studio.id, {
        name: data.name,
        description: data.description || null,
        email: data.email || null,
        phone: data.phone || null,
        address: data.address || null,
        is_active: data.is_active,
      }),
    onSuccess: () => {
      onEditModeChange(false);
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutate(form);
  };

  if (editMode) {
    return (
      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Name"
            required
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
          <Textarea
            label="Description"
            value={form.description}
            onChange={(e) =>
              setForm((f) => ({ ...f, description: e.target.value }))
            }
          />
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
          />
          <Input
            label="Phone"
            value={form.phone}
            onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
          />
          <Input
            label="Address"
            value={form.address}
            onChange={(e) =>
              setForm((f) => ({ ...f, address: e.target.value }))
            }
          />
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) =>
                setForm((f) => ({ ...f, is_active: e.target.checked }))
              }
            />
            <span className="text-sm text-neutral-700">Active</span>
          </label>
          <div className="flex gap-2">
            <Button type="submit" isLoading={isPending}>
              Save
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => onEditModeChange(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    );
  }

  return (
    <div className="mb-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-secondary font-display text-2xl font-bold">
            {studio.name}
          </h1>
          {studio.description && (
            <p className="mt-1 text-neutral-600">{studio.description}</p>
          )}
          <p className="mt-2 text-sm text-neutral-500">
            {studio.is_active ? (
              <span className="text-green-600">Active</span>
            ) : (
              <span className="text-neutral-500">Inactive</span>
            )}
          </p>
        </div>
        <Button variant="outline" onClick={() => onEditModeChange(true)}>
          Edit studio
        </Button>
      </div>
    </div>
  );
}

function OccurrenceCreateForm({
  studioId,
  onSuccess,
  onCancel,
}: {
  studioId: number;
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(10, 0, 0, 0);
  const endTime = new Date(tomorrow);
  endTime.setHours(11, 0, 0, 0);

  const { data: services, isLoading: loadingServices } = useQuery({
    queryKey: queryKeys.studio.services(studioId),
    queryFn: () => fetchStudioServices(studioId),
  });

  const [form, setForm] = useState({
    service_id: "",
    title: "",
    start_time: tomorrow.toISOString().slice(0, 16),
    end_time: endTime.toISOString().slice(0, 16),
    description: "",
    price_cents: 0,
    max_capacity: 10,
  });

  const { mutate, isPending } = useMutation({
    mutationFn: () =>
      createOccurrence({
        studio_id: studioId,
        service_id: Number(form.service_id),
        title: form.title,
        start_time: new Date(form.start_time).toISOString(),
        end_time: new Date(form.end_time).toISOString(),
        description: form.description || undefined,
        price_cents: form.price_cents,
        max_capacity: form.max_capacity,
      }),
    onSuccess,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.service_id) return;
    mutate();
  };

  if (loadingServices) {
    return (
      <Card className="mb-4">
        <Skeleton className="h-32 w-full" />
      </Card>
    );
  }

  if (!services?.length) {
    return (
      <Card className="mb-4 p-6 text-center text-neutral-600">
        <p>Create a service before adding sessions.</p>
        <Button type="button" variant="outline" className="mt-4" onClick={onCancel}>
          Close
        </Button>
      </Card>
    );
  }

  return (
    <Card className="mb-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-neutral-700">
            Service
          </span>
          <select
            required
            className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
            value={form.service_id}
            onChange={(e) =>
              setForm((f) => ({ ...f, service_id: e.target.value }))
            }
          >
            <option value="">Select a service</option>
            {services.map((service) => (
              <option key={service.id} value={service.id}>
                {service.name}
              </option>
            ))}
          </select>
        </label>
        <Input
          label="Title"
          required
          placeholder="e.g. Yoga class"
          value={form.title}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
        />
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Start"
            type="datetime-local"
            required
            value={form.start_time}
            onChange={(e) =>
              setForm((f) => ({ ...f, start_time: e.target.value }))
            }
          />
          <Input
            label="End"
            type="datetime-local"
            required
            value={form.end_time}
            onChange={(e) =>
              setForm((f) => ({ ...f, end_time: e.target.value }))
            }
          />
        </div>
        <Textarea
          label="Description"
          value={form.description}
          onChange={(e) =>
            setForm((f) => ({ ...f, description: e.target.value }))
          }
        />
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Price (cents)"
            type="number"
            min={0}
            value={form.price_cents}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                price_cents: parseInt(e.target.value, 10) || 0,
              }))
            }
          />
          <Input
            label="Max capacity"
            type="number"
            min={1}
            value={form.max_capacity}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                max_capacity: parseInt(e.target.value, 10) || 1,
              }))
            }
          />
        </div>
        <div className="flex gap-2">
          <Button type="submit" isLoading={isPending}>
            Add session
          </Button>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  );
}

function OccurrenceCard({
  occurrence,
  onDeleted,
}: {
  occurrence: OccurrenceResponse;
  onDeleted: () => void;
}) {
  const [showBookings, setShowBookings] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const { data: bookings } = useQuery({
    queryKey: queryKeys.occurrence.bookings(occurrence.id),
    queryFn: () => fetchOccurrenceBookings(occurrence.id),
    enabled: showBookings,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteOccurrence(occurrence.id),
    onSuccess: onDeleted,
  });

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-secondary font-semibold">{occurrence.title}</h3>
          <p className="text-sm text-neutral-600">
            {formatDateTime(occurrence.start_time)} · {formatPrice(occurrence.price_cents)}
          </p>
          <p className="text-xs text-neutral-500">
            {occurrence.status === "scheduled"
              ? "Scheduled"
              : occurrence.status === "completed"
                ? "Completed"
                : "Cancelled"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            onClick={() => setShowBookings((v) => !v)}
            className="px-4 py-2 text-sm"
          >
            {showBookings ? "Hide" : "Bookings"}
          </Button>
          {!confirmDelete ? (
            <Button
              variant="ghost"
              className="px-4 py-2 text-sm text-red-600 hover:text-red-700"
              onClick={() => setConfirmDelete(true)}
            >
              Delete
            </Button>
          ) : (
            <>
              <Button
                className="bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700"
                onClick={() => deleteMutation.mutate()}
                isLoading={deleteMutation.isPending}
              >
                Confirm
              </Button>
              <Button
                variant="ghost"
                className="px-4 py-2 text-sm"
                onClick={() => setConfirmDelete(false)}
              >
                Cancel
              </Button>
            </>
          )}
        </div>
      </div>
      {showBookings && (
        <div className="mt-4 border-t border-neutral-200 pt-4">
          {bookings?.length === 0 ? (
            <p className="text-sm text-neutral-600">No bookings</p>
          ) : (
            <ul className="space-y-2">
              {bookings?.map((b) => (
                <li key={b.id} className="text-sm">
                  {b.guest_name ?? b.guest_email ?? `Booking #${b.id}`} ·{" "}
                  {b.status}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Card>
  );
}
