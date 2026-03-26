"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Camera, Calendar, Trophy } from "lucide-react";
import { SectionHeading } from "@/components/SectionHeading";

const steps = [
  {
    id: "01",
    title: "Capture",
    description:
      "Browse curated studios. Use filters to find the perfect lighting, vibe, and intensity for your unique practice.",
    icon: <Camera className="h-6 w-6 text-teal-500" />,
    img: "../../step1.webp",
  },
  {
    id: "02",
    title: "Focus",
    description:
      "Secure your spot in one tap. No calls, no waiting. Just a seamless frame for your busy schedule.",
    icon: <Calendar className="h-6 w-6 text-teal-500" />,
    img: "../../step2.webp",
  },
  {
    id: "03",
    title: "Develop",
    description:
      "Show up and move. Your journey is captured in your profile, tracking every session and milestone automatically.",
    icon: <Trophy className="h-6 w-6 text-teal-500" />,
    img: "../../step3.webp",
  },
];

export const HowItWorksSection = () => {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-10%" });

  return (
    <div
      ref={containerRef}
      className="relative container mx-auto max-w-7xl px-6 pb-36"
    >
      <div className="mb-24 max-w-2xl">
        <SectionHeading size="label" className="mb-6 block text-teal-500">
          Process
        </SectionHeading>
        <SectionHeading size="section" as="h2" className="text-zinc-900">
          Your journey, <br />
          <span className="font-serif font-light text-zinc-400 italic">
            in three frames.
          </span>
        </SectionHeading>
      </div>

      <div className="relative">
        <div className="pointer-events-none absolute top-0 left-0 z-0 h-full w-full md:left-1/2 md:-translate-x-1/2">
          <svg
            width="100%"
            height="100%"
            viewBox="0 0 1000 1450"
            fill="none"
            preserveAspectRatio="none"
            className="overflow-visible"
          >
            <motion.path
              className="hidden md:block"
              d="M450 -50 C 800 150, 200 600, 500 900 C 800 1200, 200 1300, 400 1600"
              stroke="url(#line-grad)"
              strokeWidth="10"
              strokeDasharray="25 35"
              strokeLinecap="round"
              markerEnd="url(#arrowhead)"
              initial={{ pathLength: 0 }}
              animate={isInView ? { pathLength: 1 } : {}}
              transition={{ duration: 5, ease: "linear" }}
            />

            <motion.path
              className="md:hidden"
              d="M50 -25 L 40 1550"
              stroke="url(#line-grad)"
              strokeWidth="10"
              strokeDasharray="15 25"
              strokeLinecap="round"
              markerEnd="url(#arrowhead)"
              initial={{ pathLength: 0 }}
              animate={isInView ? { pathLength: 1 } : {}}
              transition={{ duration: 5, ease: "linear" }}
            />
            <defs>
              <linearGradient id="line-grad" x1="0" y1="0" x2="0" y2="1">
                <stop stopColor="#14B8A6" />
                <stop offset="1" stopColor="#0EA5E9" />
              </linearGradient>
              <marker
                id="arrowhead"
                markerWidth="12"
                markerHeight="12"
                refX="10"
                refY="6"
                orient="auto"
              >
                <motion.path
                  d="M2 2 L10 6 L2 10"
                  fill="none"
                  stroke="#0EA5E9"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </marker>
            </defs>
          </svg>
        </div>

        <div className="relative z-10 space-y-48 md:space-y-72">
          {steps.map((step, index) => (
            <StepItem key={step.id} step={step} index={index} />
          ))}
        </div>
      </div>
    </div>
  );
};

interface StepItemData {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  img: string;
}

const StepItem = ({ step, index }: { step: StepItemData; index: number }) => {
  const ref = useRef(null);
  const isStepInView = useInView(ref, { margin: "-30% 0px" });
  const isEven = index % 2 === 0;

  return (
    <div
      ref={ref}
      className={`flex flex-col items-center gap-12 md:flex-row md:gap-24 ${isEven ? "md:flex-row" : "md:flex-row-reverse"}`}
    >
      <div className="w-full md:w-1/2">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={isStepInView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 1 }}
          className="group relative border border-zinc-100 bg-white p-3 shadow-2xl"
          style={{ rotate: isEven ? "-2deg" : "2deg" }}
        >
          <div className="aspect-4/5 overflow-hidden bg-zinc-100">
            <motion.img
              src={step.img}
              alt={step.title}
              animate={{
                filter: isStepInView ? "grayscale(0%)" : "grayscale(100%)",
              }}
              transition={{ duration: 1 }}
              className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
            />
          </div>
        </motion.div>
      </div>

      <div className="relative flex w-full flex-col justify-center md:w-1/2">
        <motion.div
          initial={{ opacity: 0, x: isEven ? 20 : -20 }}
          animate={isStepInView ? { opacity: 1, x: 0 } : {}}
          className="relative p-8 md:p-12"
        >
          <div className="absolute top-0 right-0 h-12 w-12 border-t-2 border-r-2 border-zinc-100" />
          <div className="absolute bottom-0 left-0 h-12 w-12 border-b-2 border-l-2 border-teal-500/20" />

          <div className="mb-6 flex items-center gap-4">
            <div className="rounded-lg bg-zinc-950 p-3 text-white shadow-xl">
              {step.icon}
            </div>
            <span
              className="stroke-zinc-200 text-5xl font-black text-transparent"
              style={{ WebkitTextStroke: "1px #E4E4E7" }}
            >
              0{index + 1}
            </span>
          </div>

          <h3 className="mb-6 text-3xl font-bold tracking-tight text-zinc-900 md:text-4xl">
            {step.title}
          </h3>

          <p className="max-w-md text-lg leading-relaxed font-light text-zinc-500">
            {step.description}
          </p>
        </motion.div>
      </div>
    </div>
  );
};
