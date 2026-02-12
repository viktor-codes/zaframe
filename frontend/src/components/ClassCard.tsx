"use client";

import { PolaroidCard } from "./PolaroidCard";
import { Button } from "./ui/Button";
import { Chip } from "./ui/Chip";

export interface ClassCardProps {
  image: string;
  title: string;
  studio: string;
  instructor?: string;
  time: string;
  duration?: string;
  price?: string;
  spotsLeft?: number;
  level?: string;
  onBook?: () => void;
}

export function ClassCard({
  image,
  title,
  studio,
  instructor,
  time,
  duration = "60 min",
  price = "$18",
  spotsLeft,
  level = "All levels",
  onBook,
}: ClassCardProps) {
  return (
    <PolaroidCard
      image={image}
      caption={title}
      topLeft={
        <>
          <Chip tone="neutral">🕐 {time}</Chip>
          <Chip tone="neutral">{duration}</Chip>
        </>
      }
      topRight={
        spotsLeft !== undefined && spotsLeft <= 5 ? (
          <Chip tone="warning">⚡ {spotsLeft} spots</Chip>
        ) : (
          <Chip tone="brand">{price}</Chip>
        )
      }
      bottomContent={
        <>
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-zinc-700">{studio}</span>
            <span className="text-zinc-500">{level}</span>
          </div>
          {instructor != null && (
            <div className="mt-1 text-xs text-zinc-500">
              with {instructor}
            </div>
          )}
          <div className="mt-4">
            <Button className="w-full" onClick={onBook}>
              Book this class
            </Button>
          </div>
        </>
      }
    />
  );
}
