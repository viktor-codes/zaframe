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
        className="relative overflow-hidden bg-zinc-950 py-32 md:py-48"
      >
        <ManifestoSection />
      </Section>

      <Section
        id="how-it-works"
        variant="on-light"
        className="relative overflow-hidden bg-white py-32 md:py-64"
      >
        <HowItWorksSection />
      </Section>

      <Section
        id="search"
        variant="on-light"
        className="relative overflow-hidden bg-white pt-0 pb-32"
      >
        <SearchSection />
      </Section>

      <Section
        id="moments"
        variant="on-dark"
        className="relative overflow-hidden bg-zinc-950 py-32"
      >
        <Moments />
      </Section>
    </main>
  );
}
