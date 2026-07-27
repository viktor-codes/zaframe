"use client";

import { useState } from "react";
import { Heart } from "lucide-react";

export function SaveStudioButton() {
  const [saved, setSaved] = useState(false);

  return (
    <button
      type="button"
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        setSaved((prev) => !prev);
      }}
      className="flex h-9 w-9 items-center justify-center rounded-full bg-white/90 backdrop-blur-sm transition-all hover:scale-110"
      aria-label={saved ? "Unsave" : "Save"}
    >
      <Heart
        className={`h-4 w-4 ${saved ? "fill-red-500 text-red-500" : "text-zinc-400"}`}
        strokeWidth={2}
      />
    </button>
  );
}
