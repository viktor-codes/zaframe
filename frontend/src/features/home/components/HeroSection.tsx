"use client";

import { motion } from "framer-motion";
import FloatingCards from "./FloatingCards";

export const HeroSection = () => {
  return (
    <section className="relative overflow-hidden bg-zinc-50 py-12 lg:py-24">
      <div className="absolute -left-24 h-96 w-96 rounded-sm bg-teal-100/50 blur-3xl" />

      <div className="container relative mx-auto px-4">
        <div className="flex flex-col items-center lg:flex-row lg:justify-between mt-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="flex flex-1 flex-col lg:max-w-2xl"
          >
            <div className="mb-4 md:mb-2 mx-auto md:mx-0 w-fit inline-flex justify-center items-center gap-2 rounded-sm border border-teal-200 px-4 py-2 text-sm font-semibold text-teal-900 lg:inline-flex">
              <span className="">📸</span>
              <span className="font-light tracking-normal uppercase">
                Book it like a moment
              </span>
            </div>
            <h1 className="text-center md:text-left mb-6 text-5xl font-bold leading-[1.1] tracking-tight text-zinc-900 md:text-7xl">
              Ea
              <span className="font-serif italic font-light bg-linear-to-r from-lime-400 to-teal-500 bg-clip-text text-transparent px-0.5">
                Zee
              </span>{" "}
              booking
              <span className="font-serif italic ms-5 font-light tracking-normal">
                for
              </span>
              <br />
              <span className="bg-linear-to-r from-sky-500 via-teal-500 to-lime-400 bg-clip-text text-transparent">
                yoga, dance & movement
              </span>
            </h1>

            <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-zinc-600 md:text-xl lg:mx-0">
              Discover and book classes at verified studios.{" "}
              <br className="hidden md:block" />
              Every session is a{" "}
              <span className="font-semibold text-zinc-900">moment</span> worth
              capturing.
            </p>

            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row lg:justify-start">
              <button className="group relative overflow-hidden rounded-sm bg-zinc-900 px-8 py-4 text-white transition-all hover:bg-zinc-800">
                <span className="relative z-10 font-semibold">
                  Explore Studios
                </span>
                <div className="absolute inset-0 -translate-x-full bg-linear-to-r from-sky-400 to-lime-300 transition-transform duration-300 group-hover:translate-x-0" />
              </button>
              <button className="rounded-sm border border-teal-200 bg-white px-8 py-4 font-semibold text-zinc-900 transition-colors hover:bg-zinc-50">
                How it works
              </button>
            </div>
          </motion.div>

          <div className="relative flex w-full flex-1 justify-center">
            <FloatingCards />
          </div>
        </div>
      </div>
    </section>
  );
};
