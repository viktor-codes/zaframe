"use client";

import { useState } from "react";
import { Search, MapPin } from "lucide-react";
import { Button } from "@/components/ui/Button";

export interface StudiosSearchBarProps {
  category: string;
  city: string;
  onSearch: (category: string, city: string) => void;
}

export function StudiosSearchBar({
  category,
  city,
  onSearch,
}: StudiosSearchBarProps) {
  const [localCategory, setLocalCategory] = useState(category);
  const [localCity, setLocalCity] = useState(city);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(localCategory, localCity);
  };

  return (
    <form
      id="studios-search"
      onSubmit={handleSubmit}
      className="flex w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-zinc-100 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-shadow duration-200 hover:shadow-(--shadow-soft) sm:flex-row"
    >
      <div className="flex min-w-0 flex-1 items-center gap-2.5 px-4 py-3">
        <Search className="h-4 w-4 shrink-0 text-zinc-400" />
        <input
          type="text"
          placeholder="Category (yoga, boxing…)"
          value={localCategory}
          onChange={(e) => setLocalCategory(e.target.value)}
          className="min-w-0 flex-1 bg-transparent text-sm font-medium text-zinc-900 outline-none placeholder:text-zinc-400"
        />
      </div>
      <div
        className="hidden w-px shrink-0 self-stretch bg-zinc-100 sm:block"
        aria-hidden
      />
      <div className="flex min-w-0 flex-1 items-center gap-2.5 border-t border-zinc-100 px-4 py-3 sm:border-t-0 sm:border-l">
        <MapPin className="h-4 w-4 shrink-0 text-zinc-400" />
        <input
          type="text"
          placeholder="City"
          value={localCity}
          onChange={(e) => setLocalCity(e.target.value)}
          className="min-w-0 flex-1 bg-transparent text-sm font-medium text-zinc-900 outline-none placeholder:text-zinc-400"
        />
      </div>
      <div className="shrink-0 border-t border-zinc-100 px-3 py-2.5 sm:border-t-0 sm:py-2">
        <Button type="submit" size="md" className="w-full sm:w-auto">
          Search
        </Button>
      </div>
    </form>
  );
}
