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
      className="flex flex-col gap-6 pb-6 will-change-transform antialiased"
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
              className="relative p-6 rounded-3xl border border-white/20 bg-zinc-900/40 group hover:border-teal-500/30 transition-all duration-500 w-[260px] md:w-[280px] lg:w-[300px] shadow-2xl shadow-black/50"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/5 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="absolute top-4 left-4 w-2 h-2 border-t border-l border-teal-400/60 group-hover:border-teal-400 transition-colors" />

              <div className="relative z-20 text-white text-sm leading-relaxed font-light tracking-wide mb-6">
                &quot;{text}&quot;
              </div>

              <div className="relative z-10 flex items-center gap-3 pt-4 border-t border-white/10">
                <div className="relative h-10 w-10 flex-none rounded-full overflow-hidden border border-white/20 bg-zinc-800">
                  <Image
                    src={imageSrc}
                    alt={name}
                    fill
                    className="object-cover grayscale invert-[0.1] group-hover:grayscale-0 group-hover:invert-0 transition-all duration-500"
                  />
                </div>
                <div className="min-w-0">
                  <div className="font-semibold text-white text-xs tracking-tight truncate">
                    {name}
                  </div>
                  <div className="text-teal-400 text-[10px] font-mono tracking-wider truncate uppercase">
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

export const Moments = (_props: MomentsProps) => {
  const sectionView = useSectionInView();
  const inView = sectionView?.inView ?? true;

  return (
    <div className="relative h-full">
      {/* Background Layer */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <Image
          src="/dark-section-bg.jpg"
          alt="Dark Studio Background"
          fill
          className="object-cover opacity-20 grayscale"
        />
        <div className="absolute inset-0 bg-linear-to-b from-zinc-950 via-zinc-950/80 to-zinc-950" />
        <div className="absolute inset-0 bg-linear-to-r from-zinc-950 via-transparent to-zinc-950" />

        {/* Меньший blur и размер — blur-[120px] на 500px очень тяжёлый для GPU */}
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-teal-500/5 blur-[60px] rounded-full" />
        <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-sky-500/5 blur-[60px] rounded-full" />
      </div>

      <div className="container relative z-10 mx-auto px-6 max-w-7xl">
        <div className="mb-24 text-center">
          <SectionHeading size="label" className="text-teal-500 mb-8 block">
            Community
          </SectionHeading>

          <SectionHeading size="section" as="h2" className="text-white">
            Real people <br />
            <span className="relative inline-block mt-4 font-serif italic font-light text-zinc-400">
              real impact
              <svg
                className="absolute -bottom-8 left-[-10%] w-[120%] h-8"
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
              "text-zinc-400 mt-12 text-base md:text-lg max-w-2xl mx-auto font-light leading-relaxed tracking-tight",
              "transition-all duration-500 ease-out delay-200",
              inView ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2",
            )}
          >
            Our community is the heartbeat of Eazee. We curate experiences
            around the people who use them, where your{" "}
            <span className="text-white font-medium">energy and time</span> are
            the ultimate priority.
          </p>
        </div>

        {/* Колонки: inView останавливает анимацию когда секция не видна */}
        <div className="flex justify-center gap-6 md:gap-8 mask-[linear-gradient(to_bottom,transparent,black_15%,black_85%,transparent)] max-h-[700px] overflow-hidden">
          <MomentsColumn
            moments={moments.slice(0, 3)}
            duration={22}
            inView={inView}
          />
          <MomentsColumn
            moments={moments.slice(3, 6)}
            duration={28}
            className="hidden md:block mt-12"
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
