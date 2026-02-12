"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { Scan, Minimize } from "lucide-react";
import { MobileMenu, type NavLink } from "./MobileMenu";
import { ArrowRight } from "lucide-react";

const NAV_LINKS: NavLink[] = [
  { name: "Explore", href: "#explore" },
  { name: "Moments", href: "#moments" },
  { name: "Studios", href: "#studios" },
  { name: "B2B", href: "#b2b" },
];

const iconSpring = { type: "spring" as const, stiffness: 400, damping: 28 };

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-sm">
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
        <Link
          href="/"
          className="flex items-center text-xl font-bold tracking-tighter text-zinc-900"
        >
          <img
            src="/new-logo.svg"
            alt="ZeeFrame"
            width={50}
            height={50}
            className="h-10 w-10 object-contain md:h-12 md:w-12"
          />
          <span className="ml-2">
            Zee
            <span className="pr-0.5 bg-linear-to-r from-sky-600 to-teal-500 bg-clip-text text-transparent">
              Frame
            </span>
            .
          </span>
        </Link>
        <div className="flex items-center justify-center gap-4">
          {/* Desktop nav */}
          <nav className="hidden items-center gap-8 md:flex">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className="text-sm font-medium text-zinc-600 transition-colors hover:text-zinc-900"
              >
                {link.name}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-4 ms-4">
            <Link
              href="#signin"
              className="hidden rounded-sm bg-zinc-900 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 md:inline-block"
            >
              Sign in
            </Link>

            {/* Mobile menu toggle: иконка «всасывается», из неё «разъезжается» вторая */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-full text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-900 md:hidden"
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            >
              <motion.span
                className="absolute inset-0 flex items-center justify-center"
                initial={false}
                animate={{
                  scale: mobileMenuOpen ? 0 : 1,
                  opacity: mobileMenuOpen ? 0 : 1,
                }}
                transition={{
                  ...iconSpring,
                  delay: mobileMenuOpen ? 0 : 0.12,
                }}
              >
                <Scan className="h-6 w-6" />
              </motion.span>
              <motion.span
                className="absolute inset-0 flex items-center justify-center"
                initial={false}
                animate={{
                  scale: mobileMenuOpen ? 1 : 0,
                  opacity: mobileMenuOpen ? 1 : 0,
                }}
                transition={{
                  ...iconSpring,
                  delay: mobileMenuOpen ? 0.12 : 0,
                }}
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
