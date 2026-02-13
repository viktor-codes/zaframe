"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { Scan, Minimize, ArrowRight } from "lucide-react";
import { MobileMenu, type NavLink } from "./MobileMenu";

const NAV_LINKS: NavLink[] = [
  { name: "Explore", href: "#explore" },
  { name: "Moments", href: "#moments" },
  { name: "Studios", href: "#studios" },
  { name: "B2B", href: "#b2b" },
];

const iconSpring = { type: "spring" as const, stiffness: 400, damping: 28 };

export function Header({ variant = "dark" }: { variant?: "light" | "dark" }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isDark = variant === "dark";

  return (
    // Добавлена плавная смена прозрачности фона в зависимости от варианта
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${isDark ? "bg-zinc-950/20 backdrop-blur-md" : "backdrop-blur-sm"}`}
    >
      {/* Top Announcement Bar */}
      <div className="flex justify-center items-center py-2.5 bg-zinc-950 text-white text-[11px] font-bold uppercase tracking-[0.15em] gap-4 border-b border-white/5">
        <p className="text-white/50 hidden md:block">
          Revolutionizing the way you move
        </p>
        <div className="flex gap-2 items-center group cursor-pointer">
          <p className="text-teal-400 group-hover:text-teal-300 transition-colors">
            Start your EaZee journey
          </p>
          <ArrowRight className="w-3 h-3 text-teal-400 group-hover:translate-x-1 transition-transform" />
        </div>
      </div>

      <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
        {/* LOGO SECTION */}
        <Link
          href="/"
          className="flex items-center text-xl font-bold tracking-tighter transition-opacity hover:opacity-80"
        >
          <img
            src="/new-logo.svg"
            alt="ZeeFrame"
            width={50}
            height={50}
            className="h-10 w-10 object-contain md:h-12 md:w-12"
          />
          <span
            className={`ml-2 transition-colors duration-500 ${isDark ? "text-white" : "text-zinc-900"}`}
          >
            Zee
            <span className="pr-0.5 bg-linear-to-r from-sky-400 to-teal-400 bg-clip-text text-transparent">
              Frame
            </span>
            .
          </span>
        </Link>

        <div className="flex items-center justify-center gap-4">
          {/* DESKTOP NAV */}
          <nav className="hidden items-center gap-8 md:flex">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className={`text-sm font-medium transition-colors duration-500 ${
                  isDark
                    ? "text-zinc-400 hover:text-white"
                    : "text-zinc-600 hover:text-zinc-900"
                }`}
              >
                {link.name}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-4 ms-4">
            <Link
              href="#signin"
              className={`hidden rounded-lg px-5 py-2.5 text-sm font-semibold transition-all duration-500 md:inline-block ${
                isDark
                  ? "bg-white text-zinc-950 hover:bg-teal-400"
                  : "bg-zinc-900 text-white hover:bg-teal-400 hover:text-zinc-950"
              }`}
            >
              Sign in
            </Link>

            {/* Mobile menu toggle */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              className={`relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-full transition-colors ${
                isDark
                  ? "text-white hover:bg-white/10"
                  : "text-zinc-600 hover:bg-zinc-100"
              } md:hidden`}
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            >
              <motion.span
                className="absolute inset-0 flex items-center justify-center"
                animate={{
                  scale: mobileMenuOpen ? 0 : 1,
                  opacity: mobileMenuOpen ? 0 : 1,
                }}
                transition={{ ...iconSpring, delay: mobileMenuOpen ? 0 : 0.12 }}
              >
                <Scan className="h-6 w-6 " />
              </motion.span>
              <motion.span
                className="absolute inset-0 flex items-center justify-center"
                animate={{
                  scale: mobileMenuOpen ? 1 : 0,
                  opacity: mobileMenuOpen ? 1 : 0,
                }}
                transition={{ ...iconSpring, delay: mobileMenuOpen ? 0.12 : 0 }}
              >
                <Minimize className="h-6 w-6" />
              </motion.span>
            </button>
          </div>
        </div>
      </div>

      <MobileMenu
        isOpen={mobileMenuOpen}
        links={NAV_LINKS}
        onClose={() => setMobileMenuOpen(false)}
      />
    </header>
  );
}
