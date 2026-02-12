"use client";

import Image from "next/image";

export type PolaroidCardSize = "sm" | "md" | "lg";

export interface PolaroidCardProps {
  image: string;
  imageAlt?: string;
  caption?: React.ReactNode;
  children?: React.ReactNode;
  topLeft?: React.ReactNode;
  topRight?: React.ReactNode;
  bottomContent?: React.ReactNode;
  size?: PolaroidCardSize;
  className?: string;
  onClick?: () => void;
}

const sizeClasses: Record<PolaroidCardSize, string> = {
  sm: "max-w-[280px]",
  md: "max-w-[360px]",
  lg: "max-w-[440px]",
};

const imageHeightClasses: Record<PolaroidCardSize, string> = {
  sm: "h-[200px]",
  md: "h-[240px]",
  lg: "h-[320px]",
};

export function PolaroidCard({
  image,
  imageAlt = "",
  caption,
  children,
  topLeft,
  topRight,
  bottomContent,
  size = "md",
  className = "",
  onClick,
}: PolaroidCardProps) {
  const isExternalImage = image.startsWith("http") || image.startsWith("//");

  return (
    <div
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      className={`group relative w-full ${sizeClasses[size]} rounded-xl bg-white shadow-paper transition-all duration-300 hover:-translate-y-2 hover:shadow-hover ${
        onClick ? "cursor-pointer" : ""
      } ${className}`}
    >
      <div className="relative p-4 pb-3">
        <div className="relative overflow-hidden rounded-lg">
          <Image
            src={image}
            alt={imageAlt}
            width={360}
            height={size === "sm" ? 200 : size === "md" ? 240 : 320}
            className={`${imageHeightClasses[size]} w-full object-cover transition duration-500 group-hover:scale-[1.03]`}
            unoptimized={isExternalImage}
          />

          {(topLeft || topRight) && (
            <>
              <div className="absolute left-3 top-3 flex flex-wrap gap-2">
                {topLeft}
              </div>
              <div className="absolute right-3 top-3 flex flex-wrap gap-2">
                {topRight}
              </div>
            </>
          )}

          <div className="pointer-events-none absolute inset-0 bg-linear-to-t from-black/20 via-transparent to-transparent" />
        </div>
      </div>

      <div className="px-5 pb-5">
        <div className="min-h-[60px]">
          {caption != null && (
            <div className="text-[17px] font-bold tracking-tight text-zinc-900">
              {caption}
            </div>
          )}
          {children != null && (
            <div className="mt-1 text-sm text-zinc-600">{children}</div>
          )}
        </div>
        {bottomContent != null && <div className="mt-4">{bottomContent}</div>}
      </div>
    </div>
  );
}
