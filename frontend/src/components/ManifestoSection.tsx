"use client";
import { motion, useInView } from "framer-motion";
import { useRef, useEffect } from "react";
import { Search, Zap, Star } from "lucide-react";

interface ManifestoProps {
  onInView?: (isDark: boolean) => void;
}

export const ManifestoSection = ({ onInView }: ManifestoProps) => {
  const ref = useRef(null);

  // margin: "-50% 0px -50% 0px" означает, что триггер сработает,
  // когда центр секции пересечет центр экрана
  const isInView = useInView(ref, { margin: "-20% 0px -90% 0px" });

  useEffect(() => {
    if (onInView) {
      onInView(isInView);
    }
  }, [isInView, onInView]);

  const propositions = [
    {
      icon: <Search className="w-6 h-6 text-teal-400" />,
      label: "Instant Discovery",
      title: "Find your vibe in seconds",
      description:
        "No more calling studios. Browse real-time availability and filter by style.",
    },
    {
      icon: <Zap className="w-6 h-6 text-teal-400" />,
      label: "Zero Friction",
      title: "Book it like a moment",
      description:
        "See a class you love? One tap to reserve. Instant confirmation and calendar sync.",
    },
    {
      icon: <Star className="w-6 h-6 text-teal-400" />,
      label: "Curated Quality",
      title: "Only the best studios",
      description:
        "We verify every space. Real instructors, clean vibes. Only what's worth your energy.",
    },
  ];

  return (
    <section
      id="manifesto"
      ref={ref}
      className="relative py-32 md:py-48 overflow-hidden bg-zinc-950"
    >
      {/* Background Image with Overlay */}
      <div className="absolute inset-0 z-0">
        <img
          src="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&q=80&w=2000"
          alt="Dark Studio"
          className="w-full h-full object-cover opacity-30 grayscale"
        />
        {/* Градиентные маски для мягкого перехода */}
        <div className="absolute inset-0 bg-gradient-to-b from-zinc-950 via-zinc-950/80 to-zinc-950" />
        <div className="absolute inset-0 bg-gradient-to-r from-zinc-950 via-transparent to-zinc-950" />
      </div>

      {/* Neon Glow Accents */}
      <div className="absolute top-1/2 left-1/4 w-96 h-96 bg-teal-500/10 blur-[120px] rounded-full" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-sky-500/10 blur-[120px] rounded-full" />

      <div className="container relative z-10 mx-auto px-6 max-w-7xl">
        {/* Header */}
        <div className="mb-32 text-center">
          <motion.span
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : {}}
            className="text-[10px] font-black uppercase tracking-[0.5em] text-teal-500 mb-8 block"
          >
            Philosophy
          </motion.span>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            className="text-5xl md:text-7xl font-bold tracking-tighter text-white leading-[1.1]"
          >
            Made for everyone who <br />
            <span className="relative inline-block mt-4 font-serif italic font-light text-zinc-400">
              values their time
              <svg
                className="absolute -bottom-6 left-[-10%] w-[120%] h-6"
                viewBox="0 0 400 20"
                fill="none"
                preserveAspectRatio="none"
              >
                <motion.path
                  initial={{ pathLength: 0 }}
                  animate={isInView ? { pathLength: 1 } : {}}
                  transition={{ duration: 1.5, delay: 0.5 }}
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
          </motion.h2>
        </div>

        {/* Glassmorphic Grid */}
        <div className="grid gap-8 md:grid-cols-3">
          {propositions.map((value, index) => (
            <motion.div
              key={value.label}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.8, delay: 0.4 + index * 0.2 }}
              whileHover={{ y: -5 }}
              className="group relative"
            >
              {/* The Glass Card */}
              <div className="relative h-full p-10 pt-16 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl shadow-2xl transition-all duration-500 group-hover:bg-white/10 group-hover:border-white/20">
                {/* Internal Glow on Hover */}
                <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-teal-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                {/* Viewfinder Corners */}
                <div className="absolute top-6 left-6 w-4 h-4 border-t border-l border-white/20 group-hover:border-teal-400/50 transition-colors" />
                <div className="absolute bottom-6 right-6 w-4 h-4 border-b border-r border-white/20 group-hover:border-teal-400/50 transition-colors" />

                {/* Icon Container */}
                <div className="relative mb-12 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/5 border border-white/10 shadow-inner group-hover:scale-110 transition-transform duration-500">
                  {value.icon}
                </div>

                {/* Content */}
                <div className="relative space-y-6">
                  <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-teal-400/80">
                    {value.label}
                  </span>
                  <h3 className="text-2xl font-semibold text-white tracking-tight">
                    {value.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-zinc-400 font-light">
                    {value.description}
                  </p>
                </div>

                {/* Footer Detail */}
                <div className="mt-12 pt-6 border-t border-white/5 flex justify-between items-center opacity-40">
                  <span className="text-[9px] font-mono tracking-tighter text-zinc-500 tracking-[0.2em]">
                    ZF_MOMENT_0{index + 1}
                  </span>
                  <div className="flex gap-1">
                    <div className="w-1 h-1 rounded-full bg-teal-500" />
                    <div className="w-1 h-1 rounded-full bg-teal-500/40" />
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
      {/* Добавь это в самый конец внутри <section>, после контейнера */}

      {/* 1. Левый декоративный "мост" к следующей секции */}
      <div className="absolute bottom-0 left-6 md:left-12 z-20 translate-y-1/2">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          className="flex flex-col gap-0"
        >
          {/* Штрихкод - он будет наполовину на черном, наполовину на белом */}
          <div className="flex flex-col items-start bg-zinc-950 p-4 border-l border-white/20">
            <div className="flex gap-1 mb-2">
              {[2, 4, 1, 6, 2, 8, 1, 3].map((h, i) => (
                <div
                  key={i}
                  className="w-[2px] bg-white/40"
                  style={{ height: `${h * 4}px` }}
                />
              ))}
            </div>
            <span className="text-[8px] font-mono text-zinc-500 tracking-[0.3em] uppercase">
              ZeeFrame_Origin_2026
            </span>
          </div>

          {/* Силуэт фотопленки (перфорация) */}
          <div className="flex flex-col gap-2 mt-4 ml-1">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="w-4 h-6 border border-white/10 rounded-sm opacity-20"
              />
            ))}
          </div>
        </motion.div>
      </div>

      {/* 2. Правый акцент - "Серийный номер" */}
      <div className="absolute bottom-12 right-12 hidden md:block">
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 0.3 } : {}}
          className="rotate-90 origin-right text-[10px] font-mono text-white tracking-[1em] uppercase"
        >
          Verification_System_Active
        </motion.div>
      </div>
    </section>
  );
};
