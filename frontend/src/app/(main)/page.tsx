import { HeroSection } from "@/features/home/components/HeroSection";
import { HowItWorksSection } from "@/features/home/components/HowItWorksSection";
import { ManifestoSection } from "@/features/home/components/ManifestoSection";
import { Moments } from "@/features/home/components/Moments";
import { SearchSection } from "@/features/studios/components/SearchSection";
import { Header } from "@/features/navigation/components/Header";
import { Section } from "@shared/ui/section";

/**
 * Landing is composed as an RSC shell: Section (client) receives Server /
 * Client children via the children slot so static blocks (Manifesto) stay out
 * of the client graph where possible.
 */
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
