"use client";
import React from "react";
import { HeroSection } from "@/components/HeroSection";
import { ManifestoSection } from "@/components/ManifestoSection";
import { useState } from "react";
import { Header } from "@/components/Header";
import { SearchSection } from "@/components/SearchSection";
import { HowItWorksSection } from "@/components/HowItWorksSection";

export default function HomePage() {
  const [isNavDark, setIsNavDark] = useState(false);
  return (
    <main className="min-h-screen bg-white">
      <Header variant={isNavDark ? "light" : "dark"} />
      <HeroSection />
      <ManifestoSection onInView={(dark) => setIsNavDark(dark)} />
      <HowItWorksSection />
      <SearchSection />
    </main>
  );
}
