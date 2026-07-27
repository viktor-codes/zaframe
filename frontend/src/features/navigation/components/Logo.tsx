import Link from "next/link";
import Image from "next/image";
import { cn } from "@shared/lib/utils";

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
        <Image
          src="/new-logo.svg"
          alt="ZeeFrame Logo"
          width={50}
          height={50}
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
        <span className="bg-linear-to-r from-sky-600 to-teal-500 bg-clip-text pr-0.5 text-transparent">
          Frame
        </span>
        .
      </span>
    </Link>
  );
};
