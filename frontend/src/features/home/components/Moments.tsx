"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import React from "react";
import { useSectionInView } from "@/components/Section";
import { SectionHeading } from "@/components/SectionHeading";
import { cn } from "@/lib/utils";

interface Moment {
  text: string;
  imageSrc: string;
  name: string;
  username: string;
}

type MomentsProps = Record<string, never>;

// Данные (оставляем те же)
const moments: Moment[] = [
  {
    text: "As a seasoned designer always on the lookout for innovative tools, Eazee instantly grabbed my attention.",
    imageSrc: "/moments/avatar-1.png",
    name: "Jamie Rivera",
    username: "@jamietechguru00",
  },
  {
    text: "Our team's productivity has skyrocketed since we started using this tool to find studio spaces.",
    imageSrc: "/moments/avatar-2.png",
    name: "Josh Smith",
    username: "@jjsmith",
  },
  {
    text: "This app has completely transformed how I manage my projects and deadlines.",
    imageSrc: "/moments/avatar-3.png",
    name: "Morgan Lee",
    username: "@morganleewhiz",
  },
  {
    text: "I was amazed at how quickly we were able to integrate this app into our workflow.",
    imageSrc: "/moments/avatar-4.png",
    name: "Casey Jordan",
    username: "@caseyj",
  },
  {
    text: "Planning and executing events has never been easier. This app helps me keep track of all the moving parts.",
    imageSrc: "/moments/avatar-5.png",
    name: "Taylor Kim",
    username: "@taylorkimm",
  },
  {
    text: "The customizability and integration capabilities of this app are top-notch.",
    imageSrc: "/moments/avatar-6.png",
    name: "Riley Smith",
    username: "@rileysmith1",
  },
  {
    text: "Adopting this app for our team has streamlined our project management and improved communication.",
    imageSrc: "/moments/avatar-7.png",
    name: "Jordan Patels",
    username: "@jpatelsdesign",
  },
  {
    text: "With this app, we can easily assign tasks, track progress, and manage documents all in one place.",
    imageSrc: "/moments/avatar-8.png",
    name: "Sam Dawson",
    username: "@dawsontechtips",
  },
  {
    text: "Its user-friendly interface and robust features support our diverse needs.",
    imageSrc: "/moments/avatar-9.png",
    name: "Casey Harper",
    username: "@casey09",
  },
];

const MomentsColumn = ({
  moments,
  duration = 10,
  className = "",
  inView = true,
}: {
  moments: Moment[];
  duration?: number;
  className?: string;
  /** Когда false, анимация скролла приостанавливается — сильно снижает нагрузку вне viewport. */
  inView?: boolean;
}) => (
  <div className={className}>
    <motion.div
      animate={{ y: inView ? ["0%", "-50%"] : "0%" }}
      transition={{
        repeat: inView ? Infinity : 0,
        ease: "linear",
        duration: inView ? duration || 10 : 0,
      }}
      className="flex flex-col gap-6 pb-6 antialiased will-change-transform"
      style={{
        transformPerspective: "1000px",
        transformStyle: "preserve-3d",
        backfaceVisibility: "hidden",
      }}
    >
      {[...new Array(2)].fill(0).map((_, idx) => (
        <div key={`batch-${idx}`} className="flex flex-col gap-6">
          {moments.map(({ text, imageSrc, name, username }, i) => (
            <div
              key={`${name}-${idx}-${i}`}
              className="group relative w-[260px] rounded-3xl border border-white/20 bg-zinc-900/40 p-6 shadow-2xl shadow-black/50 transition-all duration-500 hover:border-teal-500/30 md:w-[280px] lg:w-[300px]"
            >
              <div className="absolute top-0 right-0 h-24 w-24 rounded-full bg-teal-500/5 opacity-0 blur-xl transition-opacity group-hover:opacity-100" />
              <div className="absolute top-4 left-4 h-2 w-2 border-t border-l border-teal-400/60 transition-colors group-hover:border-teal-400" />

              <div className="relative z-20 mb-6 text-sm leading-relaxed font-light tracking-wide text-white">
                &quot;{text}&quot;
              </div>

              <div className="relative z-10 flex items-center gap-3 border-t border-white/10 pt-4">
                <div className="relative h-10 w-10 flex-none overflow-hidden rounded-full border border-white/20 bg-zinc-800">
                  <Image
                    src={imageSrc}
                    alt={name}
                    fill
                    className="object-cover grayscale invert-[0.1] transition-all duration-500 group-hover:grayscale-0 group-hover:invert-0"
                  />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-xs font-semibold tracking-tight text-white">
                    {name}
                  </div>
                  <div className="truncate font-mono text-[10px] tracking-wider text-teal-400 uppercase">
                    {username}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ))}
    </motion.div>
  </div>
);

export const Moments = () => {
  const sectionView = useSectionInView();
  const inView = sectionView?.inView ?? true;

  return (
    <div className="relative h-full">
      {/* Background Layer */}
      <div className="pointer-events-none absolute inset-0 z-0">
        <Image
          src="/dark-section-bg.jpg"
          alt="Dark Studio Background"
          fill
          className="object-cover opacity-20 grayscale"
        />
        <div className="absolute inset-0 bg-linear-to-b from-zinc-950 via-zinc-950/80 to-zinc-950" />
        <div className="absolute inset-0 bg-linear-to-r from-zinc-950 via-transparent to-zinc-950" />

        <div className="absolute top-1/3 left-1/4 h-120 w-120 rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.15)_0%,transparent_70%)]" />
        <div className="absolute right-1/4 bottom-1/4 h-120 w-120 rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.15)_0%,transparent_70%)]" />
      </div>

      <div className="relative z-10 container mx-auto max-w-7xl px-6">
        <div className="mb-24 text-center">
          <SectionHeading size="label" className="mb-8 block text-teal-500">
            Community
          </SectionHeading>

          <SectionHeading size="section" as="h2" className="text-white">
            Real people <br />
            <span className="relative mt-4 inline-block font-serif font-light text-zinc-400 italic">
              real impact
              <svg
                className="absolute -bottom-8 left-[-10%] h-8 w-[120%]"
                viewBox="0 0 400 30"
                fill="none"
                preserveAspectRatio="none"
              >
                <path
                  d="M10 20C60 20 80 5 130 5C180 5 200 25 250 25C300 25 320 10 390 10"
                  stroke="url(#zee-wave)"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
                <defs>
                  <linearGradient
                    id="zee-wave"
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

          <p
            className={cn(
              "mx-auto mt-12 max-w-2xl text-base leading-relaxed font-light tracking-tight text-zinc-400 md:text-lg",
              "transition-all delay-200 duration-500 ease-out",
              inView ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0",
            )}
          >
            Our community is the heartbeat of Eazee. We curate experiences
            around the people who use them, where your{" "}
            <span className="font-medium text-white">energy and time</span> are
            the ultimate priority.
          </p>
        </div>

        {/* Колонки: inView останавливает анимацию когда секция не видна */}
        <div className="flex max-h-[700px] justify-center gap-6 overflow-hidden mask-[linear-gradient(to_bottom,transparent,black_15%,black_85%,transparent)] md:gap-8">
          <MomentsColumn
            moments={moments.slice(0, 3)}
            duration={22}
            inView={inView}
          />
          <MomentsColumn
            moments={moments.slice(3, 6)}
            duration={28}
            className="mt-12 hidden md:block"
            inView={inView}
          />
          <MomentsColumn
            moments={moments.slice(6, 9)}
            duration={24}
            className="hidden lg:block"
            inView={inView}
          />
        </div>
      </div>
    </div>
  );
};
