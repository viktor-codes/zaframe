"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Camera, Calendar, Trophy } from "lucide-react";

const steps = [
  {
    id: "01",
    title: "Capture",
    description:
      "Browse curated studios. Use filters to find the perfect lighting, vibe, and intensity for your unique practice.",
    icon: <Camera className="w-6 h-6 text-teal-500" />,
    img: "../../step1.webp",
  },
  {
    id: "02",
    title: "Focus",
    description:
      "Secure your spot in one tap. No calls, no waiting. Just a seamless frame for your busy schedule.",
    icon: <Calendar className="w-6 h-6 text-teal-500" />,
    img: "../../step2.webp",
  },
  {
    id: "03",
    title: "Develop",
    description:
      "Show up and move. Your journey is captured in your profile, tracking every session and milestone automatically.",
    icon: <Trophy className="w-6 h-6 text-teal-500" />,
    img: "../../step3.webp",
  },
];

export const HowItWorksSection = () => {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-10%" });

  return (
    <section
      id="how-it-works"
      ref={containerRef}
      className="py-32 md:py-64 bg-white overflow-hidden relative"
    >
      <div className="container mx-auto px-6 max-w-7xl relative">
        <div className="max-w-2xl mb-24">
          <motion.span
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : {}}
            className="text-[10px] font-black uppercase tracking-[0.4em] text-teal-500 block mb-6"
          >
            Process
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            className="text-5xl md:text-6xl font-bold tracking-tighter text-zinc-900"
          >
            Your journey, <br />
            <span className="font-serif italic font-light text-zinc-400">
              in three frames.
            </span>
          </motion.h2>
        </div>

        <div className="relative">
          <div className="absolute top-0 left-0 md:left-1/2 md:-translate-x-1/2 w-full h-full pointer-events-none z-0">
            <svg
              width="100%"
              height="100%"
              viewBox="0 0 1000 1500"
              fill="none"
              preserveAspectRatio="none"
              className="overflow-visible"
            >
              <motion.path
                className="hidden md:block"
                d="M450 -50 C 800 150, 200 600, 500 900 C 800 1200, 200 1300, 400 1600"
                stroke="#F4F4F5"
                strokeWidth="10"
                strokeDasharray="25 35"
                strokeLinecap="round"
              />
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
                d="M40 0 L 40 1500"
                stroke="#F4F4F5"
                strokeWidth="10"
                strokeDasharray="15 25"
                strokeLinecap="round"
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

          <div className="space-y-48 md:space-y-72 relative z-10">
            {steps.map((step, index) => (
              <StepItem key={step.id} step={step} index={index} />
            ))}
          </div>
        </div>
      </div>
    </section>
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
      className={`flex flex-col md:flex-row items-center gap-12 md:gap-24 
        ${isEven ? "md:flex-row" : "md:flex-row-reverse"}`}
    >
      <div className="w-full md:w-1/2">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={isStepInView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 1 }}
          className="bg-white p-3 shadow-2xl border border-zinc-100 relative group"
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
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
            />
          </div>
        </motion.div>
      </div>

      <div className="w-full md:w-1/2 flex flex-col justify-center relative">
        <motion.div
          initial={{ opacity: 0, x: isEven ? 20 : -20 }}
          animate={isStepInView ? { opacity: 1, x: 0 } : {}}
          className="p-8 md:p-12 relative"
        >
          <div className="absolute top-0 right-0 w-12 h-12 border-t-2 border-r-2 border-zinc-100" />
          <div className="absolute bottom-0 left-0 w-12 h-12 border-b-2 border-l-2 border-teal-500/20" />

          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-zinc-950 text-white rounded-lg shadow-xl">
              {step.icon}
            </div>
            <span
              className="text-5xl font-black text-transparent stroke-zinc-200"
              style={{ WebkitTextStroke: "1px #E4E4E7" }}
            >
              0{index + 1}
            </span>
          </div>

          <h3 className="text-3xl md:text-4xl font-bold mb-6 tracking-tight text-zinc-900">
            {step.title}
          </h3>

          <p className="text-lg text-zinc-500 font-light leading-relaxed max-w-md">
            {step.description}
          </p>
        </motion.div>
      </div>
    </div>
  );
};
