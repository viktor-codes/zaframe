"use client";

import Link from "next/link";
import Image from "next/image"; // Импортируем компонент Image
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
        {/* Оптимизированный Image */}
        <Image
          src="/new-logo.svg"
          alt="ZeeFrame Logo"
          // Задаем физические размеры (максимальные)
          width={50}
          height={50}
          // priority заставляет браузер загружать логотип немедленно (важно для LCP)
          priority
          className="h-10 w-10 object-contain md:h-12 md:w-12"
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
