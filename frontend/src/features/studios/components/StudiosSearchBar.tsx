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
      className="flex flex-col sm:flex-row w-full max-w-3xl rounded-2xl bg-white border border-zinc-100 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-shadow duration-200 hover:shadow-(--shadow-soft) overflow-hidden"
    >
      <div className="flex-1 flex items-center gap-2.5 px-4 py-3 min-w-0">
        <Search className="w-4 h-4 text-zinc-400 shrink-0" />
        <input
          type="text"
          placeholder="Category (yoga, boxing…)"
          value={localCategory}
          onChange={(e) => setLocalCategory(e.target.value)}
          className="flex-1 min-w-0 bg-transparent text-sm font-medium text-zinc-900 placeholder:text-zinc-400 outline-none"
        />
      </div>
      <div className="hidden sm:block w-px bg-zinc-100 self-stretch shrink-0" aria-hidden />
      <div className="flex-1 flex items-center gap-2.5 px-4 py-3 min-w-0 border-t sm:border-t-0 sm:border-l border-zinc-100">
        <MapPin className="w-4 h-4 text-zinc-400 shrink-0" />
        <input
          type="text"
          placeholder="City"
          value={localCity}
          onChange={(e) => setLocalCity(e.target.value)}
          className="flex-1 min-w-0 bg-transparent text-sm font-medium text-zinc-900 placeholder:text-zinc-400 outline-none"
        />
      </div>
      <div className="px-3 py-2.5 sm:py-2 border-t sm:border-t-0 border-zinc-100 shrink-0">
        <Button type="submit" size="md" className="w-full sm:w-auto">
          Search
        </Button>
      </div>
    </form>
  );
}
