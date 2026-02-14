"use client";

import React from "react";
import { useState } from "react";
import { HeroSection, ManifestoSection, HowItWorksSection } from "@/features/home/components";
import { SearchSection } from "@/features/studios/components";
import { Header } from "@/features/navigation/components";

export default function HomePage() {
  const [isNavDark, setIsNavDark] = useState(false);
  return (
    <main className="min-h-screen bg-white">
      <Header variant={isNavDark ? "dark" : "light"} />

      <HeroSection />
      <ManifestoSection onInView={(dark) => setIsNavDark(dark)} />
      <HowItWorksSection />
      <SearchSection />
    </main>
  );
}
