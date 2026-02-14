"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

interface LogoProps {
  variant?: "light" | "dark";
  className?: string;
}

export const Logo = ({ variant = "light", className }: LogoProps) => {
  const isDark = variant === "dark";

  return (
    <Link
      href="/"
      className={cn(
        "flex items-center text-xl font-bold tracking-tighter transition-opacity hover:opacity-90",
        className,
      )}
    >
      <div className="relative">
        <img
          src="/new-logo.svg"
          alt="ZeeFrame"
          width={50}
          height={50}
          className={cn(
            "h-10 w-10 object-contain md:h-12 md:w-12 transition-all duration-300",
            isDark && "brightness-0 invert",
          )}
        />
      </div>

      <span
        className={cn(
          "ml-2 transition-colors duration-300",
          isDark ? "text-white" : "text-zinc-900",
        )}
      >
        Zee
        <span className="pr-0.5 bg-linear-to-r from-sky-600 to-teal-500 bg-clip-text text-transparent">
          Frame
        </span>
        .
      </span>
    </Link>
  );
};
