"use client";

import { motion } from "framer-motion";
import { SectionHeading } from "@/components/SectionHeading";
import FloatingCards from "./FloatingCards";
import Link from "next/link";

export const HeroSection = () => {
  return (
    <>
      <div className="absolute -left-24 h-96 w-96 rounded-sm bg-teal-100/50 blur-3xl" />

      <div className="relative container mx-auto px-4">
        <div className="mt-24 flex flex-col items-center xl:flex-row xl:justify-between xl:gap-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="relative z-10 flex flex-1 flex-col xl:max-w-2xl"
          >
            <div className="mx-auto mb-4 inline-flex w-fit items-center justify-center gap-2 rounded-sm border border-teal-200 px-4 py-2 text-sm font-semibold text-teal-900 xl:mx-0 xl:mb-2">
              <span className="">📸</span>
              <span className="font-light tracking-normal uppercase">
                Book it like a moment
              </span>
            </div>
            <SectionHeading
              size="hero"
              as="h1"
              className="mb-6 text-center text-zinc-900 xl:text-left"
            >
              Ea
              <span className="bg-linear-to-r from-lime-400 to-teal-500 bg-clip-text pr-1.5 pl-0.5 font-serif font-light text-transparent italic">
                Zee
              </span>{" "}
              booking
              <span className="ms-5 font-serif font-light tracking-normal italic">
                for
              </span>
              <br />
              <span className="bg-linear-to-r from-sky-500 via-teal-500 to-lime-400 bg-clip-text text-transparent">
                yoga, dance & movement
              </span>
            </SectionHeading>

            <p className="mb-10 max-w-2xl text-center text-lg leading-relaxed text-zinc-600 md:text-xl xl:mx-0 xl:text-left">
              Discover and book classes at verified studios.{" "}
              <br className="hidden md:block" />
              Every session is a{" "}
              <span className="font-semibold text-zinc-900">moment</span> worth
              capturing.
            </p>

            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row xl:justify-start">
              {/* Обернули первую кнопку в Link */}
              <Link
                href="/studios"
                className="group relative w-full cursor-pointer overflow-hidden rounded-sm bg-zinc-900 px-8 py-4 text-center text-white transition-all hover:scale-105 sm:w-auto"
              >
                <span className="relative z-10 font-semibold">
                  Explore Studios
                </span>
              </Link>

              <a
                href="#how-it-works"
                className="flex w-full items-center justify-center rounded-sm border border-teal-200 bg-white px-8 py-4 text-center font-semibold text-zinc-900 hover:scale-105 sm:w-auto"
              >
                How it works
              </a>
            </div>
          </motion.div>

          <div className="relative z-0 flex w-full min-w-0 flex-1 justify-center">
            <FloatingCards />
          </div>
        </div>
      </div>
    </>
  );
};
