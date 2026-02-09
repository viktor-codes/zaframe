"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, Button, Input, Textarea } from "@/components/ui";
import { createStudio } from "@/lib/api";

export default function NewStudioPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    name: "",
    description: "",
    email: "",
    phone: "",
    address: "",
  });
  const [error, setError] = useState<string | null>(null);

  const { mutate, isPending } = useMutation({
    mutationFn: createStudio,
    onSuccess: (studio) => {
      queryClient.invalidateQueries({ queryKey: ["studios"] });
      router.push(`/dashboard/studios/${studio.id}`);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Failed to create studio");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    mutate({
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      email: form.email.trim() || undefined,
      phone: form.phone.trim() || undefined,
      address: form.address.trim() || undefined,
    });
  };

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <Link
        href="/dashboard"
        className="text-primary hover:text-primary-dark text-sm font-medium mb-6 inline-block"
      >
        ← Back to dashboard
      </Link>
      <h1 className="font-display font-bold text-2xl text-secondary mb-6">
        Create studio
      </h1>
      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Name"
            required
            placeholder="Studio name"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
          <Textarea
            label="Description"
            placeholder="Description of your studio"
            value={form.description}
            onChange={(e) =>
              setForm((f) => ({ ...f, description: e.target.value }))
            }
          />
          <Input
            label="Email"
            type="email"
            placeholder="studio@example.com"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
          />
          <Input
            label="Phone"
            type="tel"
            placeholder="+1 234 567 8900"
            value={form.phone}
            onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
          />
          <Input
            label="Address"
            placeholder="123 Main St, City"
            value={form.address}
            onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
          />
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-red-800">
              {error}
            </div>
          )}
          <div className="flex gap-4 justify-end">
            <Button variant="outline" asChild type="button">
              <Link href="/dashboard">Cancel</Link>
            </Button>
            <Button type="submit" isLoading={isPending}>
              Create studio
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
