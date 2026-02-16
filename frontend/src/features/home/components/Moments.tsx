"use client";

import { motion, useInView } from "framer-motion";
import Image from "next/image";
import React, { useRef } from "react";
import { SectionHeading } from "@/components/SectionHeading";

interface Moment {
  text: string;
  imageSrc: string;
  name: string;
  username: string;
}

interface MomentsProps {}

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
}: {
  moments: Moment[];
  duration?: number;
  className?: string;
}) => (
  <div className={className}>
    <motion.div
      animate={{ y: ["0%", "-50%"] }}
      transition={{
        repeat: Infinity,
        ease: "linear",
        duration: duration || 10,
      }}
      className="flex flex-col gap-6 pb-6 will-change-transform antialiased"
      style={{
        transformPerspective: "1000px",
        transformStyle: "preserve-3d", // Safari fix
        backfaceVisibility: "hidden", // Safari fix
      }}
    >
      {[...new Array(2)].fill(0).map((_, idx) => (
        <div key={`batch-${idx}`} className="flex flex-col gap-6">
          {moments.map(({ text, imageSrc, name, username }, i) => (
            <div
              key={`${name}-${idx}-${i}`}
              className="relative p-6 rounded-3xl border border-white/20 bg-zinc-900/40 group hover:border-teal-500/30 transition-all duration-500 w-[260px] md:w-[280px] lg:w-[300px] shadow-2xl shadow-black/50"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/5 blur-2xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
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
  const contentRef = useRef<HTMLDivElement>(null);
  const contentVisible = useInView(contentRef, { once: true, amount: 0.2 });

  return (
    <div className="relative h-full">
      {/* Background Layer */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <Image
          src="/moments-bg.webp"
          alt="Dark Studio Background"
          fill
          className="object-cover opacity-20 grayscale"
        />
        <div className="absolute inset-0 bg-linear-to-b from-zinc-950 via-zinc-950/80 to-zinc-950" />
        <div className="absolute inset-0 bg-linear-to-r from-zinc-950 via-transparent to-zinc-950" />

        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-teal-500/5 blur-[120px] rounded-full" />
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-sky-500/5 blur-[120px] rounded-full" />
      </div>

      <div ref={contentRef} className="container relative z-10 mx-auto px-6 max-w-7xl">
        <div className="mb-24 text-center">
          <motion.span
            initial={{ opacity: 0 }}
            animate={contentVisible ? { opacity: 1 } : {}}
            className="block"
          >
            <SectionHeading size="label" className="text-teal-500 mb-8 block">
              Community
            </SectionHeading>
          </motion.span>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={contentVisible ? { opacity: 1, y: 0 } : {}}
          >
            <SectionHeading size="section" as="h2" className="text-white">
              Real people <br />
            <span className="relative inline-block mt-4 font-serif italic font-light text-zinc-400">
              real impact
              {/* Графический элемент "Zee" */}
              <svg
                className="absolute -bottom-8 left-[-10%] w-[120%] h-8"
                viewBox="0 0 400 30"
                fill="none"
                preserveAspectRatio="none"
              >
                <motion.path
                  initial={{ pathLength: 0 }}
                  animate={contentVisible ? { pathLength: 1 } : {}}
                  transition={{ duration: 2, delay: 0.5 }}
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
          </motion.div>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={contentVisible ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.2 }}
            className="text-zinc-400 mt-12 text-base md:text-lg max-w-2xl mx-auto font-light leading-relaxed tracking-tight"
          >
            Our community is the heartbeat of Eazee. We curate experiences
            around the people who use them, where your{" "}
            <span className="text-white font-medium">energy and time</span> are
            the ultimate priority.
          </motion.p>
        </div>

        {/* Колонки */}
        <div className="flex justify-center gap-6 md:gap-8 [mask-image:linear-gradient(to_bottom,transparent,black_15%,black_85%,transparent)] max-h-[700px] overflow-hidden">
          <MomentsColumn moments={moments.slice(0, 3)} duration={22} />
          <MomentsColumn
            moments={moments.slice(3, 6)}
            duration={28}
            className="hidden md:block mt-12"
          />
          <MomentsColumn
            moments={moments.slice(6, 9)}
            duration={24}
            className="hidden lg:block"
          />
        </div>
      </div>

      {/* ZeeFrame декор */}
      <div className="absolute bottom-12 left-6 md:left-12 z-20 pointer-events-none opacity-20">
        <div className="flex flex-col items-start bg-zinc-950 p-4 border-l border-white/20">
          <span className="text-[8px] font-mono text-zinc-500 tracking-[0.3em] uppercase">
            Zee_Moment_Signature_2026
          </span>
        </div>
      </div>
    </div>
  );
};
