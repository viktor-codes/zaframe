"use client";

import { PolaroidCard } from "./PolaroidCard";
import { Chip } from "./ui/Chip";

export interface InstructorCardProps {
  image: string;
  name: string;
  specialties?: string[];
  rating?: number;
  classes?: number;
  bio?: string;
}

export function InstructorCard({
  image,
  name,
  specialties = [],
  rating = 4.9,
  classes = 120,
  bio,
}: InstructorCardProps) {
  return (
    <PolaroidCard
      image={image}
      caption={name}
      size="sm"
      topRight={<Chip tone="neutral">⭐ {rating}</Chip>}
      bottomContent={
        <>
          <div className="flex flex-wrap gap-2">
            {specialties.slice(0, 2).map((s, i) => (
              <Chip key={i} size="xs" tone="brand">
                {s}
              </Chip>
            ))}
          </div>
          {bio != null && (
            <p className="mt-2 text-xs leading-relaxed text-zinc-600">{bio}</p>
          )}
          <div className="mt-3 text-xs text-zinc-500">
            {classes} classes taught
          </div>
        </>
      }
    />
  );
}
