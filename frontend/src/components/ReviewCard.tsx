"use client";

import Image from "next/image";

export interface ReviewCardProps {
  author: string;
  rating: number;
  date: string;
  text: string;
  image: string;
}

export function ReviewCard({
  author,
  rating,
  date,
  text,
  image,
}: ReviewCardProps) {
  const isExternalImage =
    image.startsWith("http") || image.startsWith("//");

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <Image
          src={image}
          alt={author}
          width={48}
          height={48}
          className="h-12 w-12 rounded-full object-cover"
          unoptimized={isExternalImage}
        />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <div className="font-semibold text-zinc-900">{author}</div>
            <div className="flex items-center gap-1 text-sm">
              <span>⭐</span>
              <span className="font-semibold">{rating}</span>
            </div>
          </div>
          <div className="text-xs text-zinc-500">{date}</div>
          <p className="mt-2 text-sm leading-relaxed text-zinc-700">{text}</p>
        </div>
      </div>
    </div>
  );
}
