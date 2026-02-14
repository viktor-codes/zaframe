"use client";

import { Button } from "@/components/ui/Button";

export interface SearchBarProps {
  onSearch?: (params: { location?: string; date?: string; activity?: string }) => void;
  defaultValue?: { location?: string; date?: string; activity?: string };
  className?: string;
}

export function SearchBar({
  onSearch,
  defaultValue,
  className = "",
}: SearchBarProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const location = (form.elements.namedItem("location") as HTMLInputElement)?.value;
    const date = (form.elements.namedItem("date") as HTMLInputElement)?.value;
    const activity = (form.elements.namedItem("activity") as HTMLInputElement)?.value;
    onSearch?.({ location, date, activity });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`flex w-full max-w-[800px] items-center gap-2 rounded-full border border-zinc-200 bg-white px-4 py-3 shadow-sm transition hover:shadow-md ${className}`}
    >
      <input
        name="location"
        placeholder="City or studio"
        defaultValue={defaultValue?.location}
        className="w-full bg-transparent text-sm outline-none placeholder:text-zinc-400"
      />
      <div className="hidden h-6 w-px bg-zinc-200 md:block" />
      <input
        name="date"
        type="date"
        defaultValue={defaultValue?.date}
        className="hidden w-[140px] bg-transparent text-sm outline-none placeholder:text-zinc-400 md:block"
      />
      <div className="hidden h-6 w-px bg-zinc-200 md:block" />
      <input
        name="activity"
        placeholder="Yoga, dance, pilates..."
        defaultValue={defaultValue?.activity}
        className="hidden w-[160px] bg-transparent text-sm outline-none placeholder:text-zinc-400 md:block"
      />
      <Button type="submit">Search</Button>
    </form>
  );
}
