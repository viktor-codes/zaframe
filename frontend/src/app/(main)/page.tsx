"use client";

import React from "react";
import {
  HeroSection,
  ManifestoSection,
  HowItWorksSection,
} from "@/features/home/components";
import { SearchSection } from "@/features/studios/components";
import { Header } from "@/features/navigation/components";
import { Moments } from "@/features/home/components/Moments";
import { Section } from "@/components/Section";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      <Header />

      <Section
        id="hero"
        variant="on-light"
        className="relative overflow-hidden bg-zinc-50 py-12 lg:py-24"
      >
        <HeroSection />
      </Section>

      <Section
        id="manifesto"
        variant="on-dark"
        className="relative py-32 md:py-48 bg-zinc-950 overflow-hidden"
      >
        <ManifestoSection />
      </Section>

      <Section
        id="how-it-works"
        variant="on-light"
        className="py-32 md:py-64 bg-white overflow-hidden relative"
      >
        <HowItWorksSection />
      </Section>

      <Section
        id="search"
        variant="on-light"
        className="relative bg-white pt-0 pb-32 overflow-hidden"
      >
        <SearchSection />
      </Section>

      <Section
        id="moments"
        variant="on-dark"
        className="relative py-32 bg-zinc-950 overflow-hidden"
      >
        <Moments />
      </Section>
    </main>
  );
}
