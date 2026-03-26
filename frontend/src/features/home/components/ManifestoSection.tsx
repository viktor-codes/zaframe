"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import { Search, Zap, Star } from "lucide-react";
import { SectionHeading } from "@/components/SectionHeading";

const PROPOSITIONS = [
  {
    icon: "Search" as const,
    label: "Instant Discovery",
    title: "Find your vibe in seconds",
    description:
      "No more calling studios. Browse real-time availability and filter by style.",
  },
  {
    icon: "Zap",
    label: "Zero Friction",
    title: "Book it like a moment",
    description:
      "See a class you love? One tap to reserve. Instant confirmation and calendar sync.",
  },
  {
    icon: "Star",
    label: "Curated Quality",
    title: "Only the best studios",
    description:
      "We verify every space. Real instructors, clean vibes. Only what's worth your energy.",
  },
] as const;

const ICONS = { Search, Zap, Star };

export const ManifestoSection = () => {
  const propositions = PROPOSITIONS;

  return (
    <div className="relative h-full">
      <div className="pointer-events-none inset-0 overflow-hidden">
        <div className="inset-0 z-0">
          <Image
            src="/dark-section-bg.jpg"
            alt="Dark Studio Background"
            fill
            className="object-cover opacity-15 grayscale"
            loading="lazy"
            sizes="100vw"
          />
          <div className="absolute inset-0 bg-linear-to-b from-zinc-950 to-zinc-950/30" />
          <div className="absolute inset-0 bg-linear-to-r from-zinc-950 via-transparent to-zinc-950" />
        </div>
        {/* Уменьшенный blur — blur-[120px] на больших div очень тяжёлый для GPU */}
        {/* <div className="absolute top-1/2 left-1/4 w-64 h-64 bg-teal-500/10 blur-2xl rounded-full" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-sky-500/10 blur-2xl rounded-full" /> */}

        <div className="absolute top-1/2 left-1/4 h-120 w-120 rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.15)_0%,transparent_70%)]" />
        <div className="absolute right-1/4 bottom-1/4 h-120 w-120 rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.15)_0%,transparent_70%)]" />
      </div>

      <div className="relative z-10 container mx-auto max-w-7xl px-6">
        <div className="mb-32 text-center">
          <SectionHeading size="label" className="mb-8 block text-teal-500">
            Philosophy
          </SectionHeading>

          <SectionHeading size="section" as="h2" className="text-white">
            Made for everyone who <br />
            <span className="relative mt-4 inline-block font-serif font-light text-zinc-400 italic">
              values their time
              <svg
                className="absolute -bottom-6 left-[-10%] h-6 w-[120%]"
                viewBox="0 0 400 20"
                fill="none"
                preserveAspectRatio="none"
              >
                <path
                  d="M1 11C40 11 50 2 90 2C130 2 140 11 180 11C220 11 230 2 270 2C310 2 320 11 399 11"
                  stroke="url(#neon-wave)"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
                <defs>
                  <linearGradient
                    id="neon-wave"
                    x1="0"
                    y1="0"
                    x2="400"
                    y2="0"
                    gradientUnits="userSpaceOnUse"
                  >
                    <stop stopColor="#0EA5E9" />
                    <stop offset="0.5" stopColor="#14B8A6" />
                    <stop offset="1" stopColor="#A3E635" />
                  </linearGradient>
                </defs>
              </svg>
            </span>
          </SectionHeading>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {propositions.map((value, index) => (
            <div
              key={value.label}
              className={`group relative ${
                // На планшете (md) первая карточка растягивается на 2 колонки
                // На десктопе (lg) снова занимает одну
                index === 0 ? "md:col-span-2 lg:col-span-1" : "col-span-1"
              }`}
            >
              <div className="relative h-full rounded-3xl border border-white/10 bg-white/[0.07] p-10 pt-16 shadow-xl backdrop-blur-2xl transition-all duration-500 group-hover:border-white/20 group-hover:bg-white/10">
                <div className="absolute inset-0 rounded-3xl bg-linear-to-br from-teal-500/5 to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

                <div className="absolute top-6 left-6 h-4 w-4 border-t border-l border-white/20 transition-colors group-hover:border-teal-400/50" />
                <div className="absolute right-6 bottom-6 h-4 w-4 border-r border-b border-white/20 transition-colors group-hover:border-teal-400/50" />

                <div className="relative mb-12 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/5 shadow-inner transition-transform duration-500 group-hover:scale-110">
                  {(() => {
                    const Icon = ICONS[value.icon];
                    return <Icon className="h-6 w-6 text-teal-400" />;
                  })()}
                </div>

                <div className="relative space-y-6">
                  <span className="text-[10px] font-bold tracking-[0.3em] text-teal-400/80 uppercase">
                    {value.label}
                  </span>
                  <h3 className="text-2xl font-semibold tracking-tight text-white">
                    {value.title}
                  </h3>
                  <p className="text-sm leading-relaxed font-light text-zinc-400">
                    {value.description}
                  </p>
                </div>

                <div className="mt-12 flex items-center justify-between border-t border-white/5 pt-6 opacity-40">
                  <span className="font-mono text-[9px] tracking-tighter text-zinc-500">
                    ZF_MOMENT_0{index + 1}
                  </span>
                  <div className="flex gap-1">
                    <div className="h-1 w-1 rounded-full bg-teal-500" />
                    <div className="h-1 w-1 rounded-full bg-teal-500/40" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
