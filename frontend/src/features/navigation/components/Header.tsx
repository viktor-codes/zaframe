"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { Scan, Minimize, ArrowRight, Search } from "lucide-react";
import { useUIStore } from "@/store/useUIStore";
import { HEADER_HEIGHT_PX } from "@/lib/constants/layout";
import { MobileMenu, type NavLink } from "./MobileMenu";
import { Logo } from "./Logo";

const NAV_LINKS: NavLink[] = [
  { name: "Explore", href: "/studios" },
  { name: "Moments", href: "/#moments" },
  { name: "B2B", href: "/#b2b" },
];

const iconSpring = { type: "spring" as const, stiffness: 400, damping: 28 };

export interface HeaderProps {
  minimalSearch?: { href: string; placeholder: string };
}

export function Header({ minimalSearch }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const headerVariant = useUIStore((state) => state.headerVariant);
  const isDark = headerVariant === "on-dark";

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-500"
      style={{ minHeight: HEADER_HEIGHT_PX }}
    >
      {/* СЛОЙ ФОНА (Blur Layer) */}
      <div
        className={`absolute inset-0 -z-10 transition-all duration-500 ${
          isDark
            ? "bg-zinc-950/20 backdrop-blur-xs"
            : "bg-zinc-50/20 backdrop-blur-xs"
        }`}
      />
      <div className="flex justify-center items-center py-2.5 bg-zinc-950 text-white text-[11px] font-bold uppercase tracking-[0.15em] gap-4 border-b border-white/5">
        <p className="text-white/50 hidden md:block">
          Revolutionizing the way you move
        </p>
        <Link
          href="/studios"
          className="flex gap-2 items-center group w-fit cursor-pointer"
        >
          <p className="text-teal-400 group-hover:text-teal-300 transition-colors">
            Start your EaZee journey
          </p>
          <ArrowRight className="w-3 h-3 text-teal-400 group-hover:translate-x-1 transition-transform" />
        </Link>
      </div>

      <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
        <Logo variant={isDark ? "dark" : "light"} />

        <div className="flex items-center justify-center gap-4">
          <nav className="hidden items-center gap-8 md:flex">
            {NAV_LINKS.map((link) => {
              const isAnchor = link.href.startsWith("#");

              // Если это якорь, используем <a>, если страница — <Link>
              const Component = isAnchor ? "a" : Link;

              return (
                <Component
                  key={link.name}
                  href={link.href}
                  // Для якорей добавляем плавный скролл
                  onClick={() => {
                    if (isAnchor) {
                      // Опционально: предотвращаем дефолт и скроллим плавно
                      // e.preventDefault();
                      // document.querySelector(link.href)?.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}
                  className={`text-sm font-medium transition-colors duration-500 cursor-pointer ${
                    isDark
                      ? "text-zinc-400 hover:text-white"
                      : "text-zinc-600 hover:text-zinc-900"
                  }`}
                >
                  {link.name}
                </Component>
              );
            })}
          </nav>

          <div className="flex items-center gap-4 ms-4">
            {minimalSearch && (
              <Link
                href={minimalSearch.href}
                className={`hidden md:flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition-colors ${
                  isDark
                    ? "border-white/20 text-zinc-400 hover:border-white/40 hover:text-white"
                    : "border-zinc-200 text-zinc-500 hover:border-zinc-300 hover:text-zinc-700"
                }`}
              >
                <Search className="w-4 h-4 shrink-0" />
                <span>{minimalSearch.placeholder}</span>
              </Link>
            )}
            <Link
              href="#signin"
              className={`hidden rounded-lg px-5 py-2.5 text-sm font-semibold transition-all duration-500 md:inline-block ${
                isDark
                  ? "bg-white text-zinc-950 hover:scale-105 transition-all duration-300"
                  : "bg-zinc-900 text-white hover:scale-105 transition-all duration-300"
              }`}
            >
              Sign in
            </Link>

            <button
              type="button"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              className={`relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-full transition-colors ${
                isDark ? "text-white" : "text-zinc-950"
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
