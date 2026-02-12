"use client";
import React from "react";
import { motion } from "framer-motion";
import { HeroSection } from "@/components/HeroSection";
import { ManifestoSection } from "@/components/ManifestoSection";
import { useState } from "react";
import { Header } from "@/components/Header";

export default function HomePage() {
  const [isNavDark, setIsNavDark] = useState(false);
  return (
    <main className="min-h-screen bg-white">
      <Header variant={isNavDark ? "dark" : "light"} />
      <HeroSection />
      <ManifestoSection onInView={(dark) => setIsNavDark(dark)} />
    </main>
  );
}
