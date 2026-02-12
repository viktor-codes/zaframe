"use client";

import { PolaroidCard } from "./PolaroidCard";
import { Button } from "./ui/Button";
import { Chip } from "./ui/Chip";
import { Badge } from "./ui/Badge";

export interface StudioCardProps {
  image: string;
  name: string;
  location: string;
  tags?: string[];
  rating?: number;
  distance?: string;
  verified?: boolean;
  onBook?: () => void;
  onSchedule?: () => void;
}

export function StudioCard({
  image,
  name,
  location,
  tags = [],
  rating = 4.9,
  distance = "8 min",
  verified = true,
  onBook,
  onSchedule,
}: StudioCardProps) {
  return (
    <PolaroidCard
      image={image}
      caption={name}
      topLeft={
        <>
          <Chip tone="neutral">⭐ {rating}</Chip>
          <Chip tone="neutral">🚶 {distance}</Chip>
        </>
      }
      topRight={verified ? <Badge variant="verified">Verified</Badge> : null}
      bottomContent={
        <>
          <div className="text-sm text-zinc-600">{location}</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {tags.slice(0, 3).map((tag, i) => (
              <Chip key={i} size="xs">
                {tag}
              </Chip>
            ))}
          </div>
          <div className="mt-4 flex gap-2">
            <Button className="flex-1" onClick={onBook}>
              Book
            </Button>
            <Button variant="secondary" className="flex-1" onClick={onSchedule}>
              Schedule
            </Button>
          </div>
        </>
      }
    />
  );
}
