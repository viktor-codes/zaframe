"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Card, Button, Input, Textarea, Skeleton } from "@/components/ui";
import {
  fetchStudio,
  fetchStudioSlots,
  updateStudio,
  createSlot,
  deleteSlot,
  fetchSlotBookings,
} from "@/lib/api";

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
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const id = Number(params.id);

  const [editMode, setEditMode] = useState(false);
  const [showAddSlot, setShowAddSlot] = useState(false);

  const { data: studio, isLoading } = useQuery({
    queryKey: ["studio", id],
    queryFn: () => fetchStudio(id),
    enabled: !Number.isNaN(id),
  });

  const { data: slots } = useQuery({
    queryKey: ["studio", id, "slots"],
    queryFn: () => fetchStudioSlots(id, { limit: 100 }),
    enabled: !!studio,
  });

  if (Number.isNaN(id)) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-red-800">
          Invalid studio
        </div>
      </div>
    );
  }

  if (isLoading || !studio) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <Skeleton className="h-8 w-48 mb-6" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (user && studio.owner_id !== user.id) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-red-800">
          <p className="font-semibold">Access denied</p>
          <p className="text-sm mt-1">You don&apos;t have permission to manage this studio.</p>
          <Link href="/dashboard" className="text-primary underline mt-2 inline-block">
            Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <Link
        href="/dashboard"
        className="text-primary hover:text-primary-dark text-sm font-medium mb-6 inline-block"
      >
        ← Back to dashboard
      </Link>

      <StudioEditForm
        studio={studio}
        editMode={editMode}
        onEditModeChange={setEditMode}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ["studio", id] })}
      />

      <section className="mt-10">
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-display font-semibold text-xl text-secondary">
            Slots (schedule)
          </h2>
          <Button onClick={() => setShowAddSlot((v) => !v)}>
            {showAddSlot ? "Cancel" : "Add slot"}
          </Button>
        </div>

        {showAddSlot && (
          <SlotCreateForm
            studioId={id}
            onSuccess={() => {
              queryClient.invalidateQueries({ queryKey: ["studio", id, "slots"] });
              setShowAddSlot(false);
            }}
            onCancel={() => setShowAddSlot(false)}
          />
        )}

        <div className="space-y-4 mt-4">
          {slots?.length === 0 ? (
            <Card className="p-8 text-center text-neutral-600">
              No slots yet. Add a slot to accept bookings.
            </Card>
          ) : (
            slots?.map((slot) => (
              <SlotCard
                key={slot.id}
                slot={slot}
                onDeleted={() =>
                  queryClient.invalidateQueries({ queryKey: ["studio", id, "slots"] })
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
  studio: { id: number; name: string; description?: string | null; email?: string | null; phone?: string | null; address?: string | null; is_active: boolean };
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
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
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
            onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
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
      <div className="flex justify-between items-start">
        <div>
          <h1 className="font-display font-bold text-2xl text-secondary">
            {studio.name}
          </h1>
          {studio.description && (
            <p className="text-neutral-600 mt-1">{studio.description}</p>
          )}
          <p className="text-sm text-neutral-500 mt-2">
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

function SlotCreateForm({
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

  const [form, setForm] = useState({
    title: "",
    start_time: tomorrow.toISOString().slice(0, 16),
    end_time: endTime.toISOString().slice(0, 16),
    description: "",
    price_cents: 0,
    max_capacity: 10,
  });

  const { mutate, isPending } = useMutation({
    mutationFn: () =>
      createSlot({
        studio_id: studioId,
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
    mutate();
  };

  return (
    <Card className="mb-4">
      <form onSubmit={handleSubmit} className="space-y-4">
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
            onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
          />
          <Input
            label="End"
            type="datetime-local"
            required
            value={form.end_time}
            onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))}
          />
        </div>
        <Textarea
          label="Description"
          value={form.description}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
        />
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Price (cents)"
            type="number"
            min={0}
            value={form.price_cents}
            onChange={(e) =>
              setForm((f) => ({ ...f, price_cents: parseInt(e.target.value, 10) || 0 }))
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
            Add slot
          </Button>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  );
}

function SlotCard({
  slot,
  onDeleted,
}: {
  slot: { id: number; title: string; start_time: string; end_time: string; price_cents: number; is_active: boolean };
  onDeleted: () => void;
}) {
  const [showBookings, setShowBookings] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const { data: bookings } = useQuery({
    queryKey: ["slot", slot.id, "bookings"],
    queryFn: () => fetchSlotBookings(slot.id),
    enabled: showBookings,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteSlot(slot.id),
    onSuccess: onDeleted,
  });

  return (
    <Card>
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-secondary">{slot.title}</h3>
          <p className="text-sm text-neutral-600">
            {formatDateTime(slot.start_time)} · {formatPrice(slot.price_cents)}
          </p>
          <p className="text-xs text-neutral-500">
            {slot.is_active ? "Active" : "Inactive"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            onClick={() => setShowBookings((v) => !v)}
            className="py-2 px-4 text-sm"
          >
            {showBookings ? "Hide" : "Bookings"}
          </Button>
          {!confirmDelete ? (
            <Button
              variant="ghost"
              className="text-red-600 hover:text-red-700 py-2 px-4 text-sm"
              onClick={() => setConfirmDelete(true)}
            >
              Delete
            </Button>
          ) : (
            <>
              <Button
                className="bg-red-600 hover:bg-red-700 text-white py-2 px-4 text-sm"
                onClick={() => deleteMutation.mutate()}
                isLoading={deleteMutation.isPending}
              >
                Confirm
              </Button>
              <Button
                variant="ghost"
                className="py-2 px-4 text-sm"
                onClick={() => setConfirmDelete(false)}
              >
                Cancel
              </Button>
            </>
          )}
        </div>
      </div>
      {showBookings && (
        <div className="mt-4 pt-4 border-t border-neutral-200">
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
