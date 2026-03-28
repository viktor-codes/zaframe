"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, ArrowRight, MapPin, Navigation } from "lucide-react";
import { useSectionInView } from "@/components/Section";
import { SectionHeading } from "@/components/SectionHeading";
import { cn } from "@/lib/utils";

const SUGGESTION_TO_CATEGORY: Record<string, string> = {
  yoga: "yoga",
  "yoga flow": "yoga",
  boxing: "boxing",
  "power boxing": "boxing",
  pilates: "pilates",
  "reformer pilates": "pilates",
  hiit: "hiit",
  "hiit blast": "hiit",
  dance: "dance",
  "contemporary dance": "dance",
  martial_arts: "martial_arts",
  "martial arts": "martial_arts",
  strength: "strength",
};

export const SearchSection = () => {
  const router = useRouter();
  const sectionView = useSectionInView();
  const inView = sectionView?.inView ?? true;

  const [activity, setActivity] = useState("");
  const [location, setLocation] = useState("");
  const [isNavigating, setIsNavigating] = useState(false);
  const [activeField, setActiveField] = useState<
    "activity" | "location" | null
  >(null);

  const suggestions = {
    activity: [
      "Yoga Flow",
      "Power Boxing",
      "Reformer Pilates",
      "HIIT Blast",
      "Contemporary Dance",
    ],
    location: [
      "Downtown",
      "West End",
      "Studio District",
      "Green Park",
      "Brooklyn Heights",
    ],
  };

  return (
    <>
      <div className="relative z-10 container mx-auto max-w-5xl px-6">
        <div className="mb-20 text-left md:mb-32 md:text-center">
          <SectionHeading
            size="section"
            as="h2"
            className="leading-[0.9] text-zinc-900"
          >
            Ready to find <br />
            <span className="font-serif font-light text-zinc-400 italic">
              your frame?
            </span>
          </SectionHeading>
        </div>

        <div
          className={cn(
            "relative w-full transition-all delay-200 duration-500 ease-out",
            inView ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0",
          )}
        >
          <div className="relative flex flex-col items-stretch rounded-2xl border border-zinc-100 bg-zinc-50 p-2 shadow-sm transition-all duration-500 focus-within:bg-white focus-within:shadow-xl md:flex-row">
            <div className="relative flex flex-1 items-center border-b border-zinc-200/50 px-6 py-4 md:border-r md:border-b-0">
              <Search className="mr-4 h-5 w-5 text-zinc-400" />

              <div className="flex-1">
                <span className="mb-1 block text-[9px] font-bold tracking-wider text-zinc-400 uppercase">
                  What to do?
                </span>

                <input
                  type="text"
                  placeholder="Yoga, Boxing, Dance..."
                  value={activity}
                  onFocus={() => setActiveField("activity")}
                  onChange={(e) => setActivity(e.target.value)}
                  className="w-full bg-transparent text-lg font-medium text-zinc-900 placeholder:text-zinc-300 focus:outline-none"
                />
              </div>
            </div>

            <div className="relative flex flex-1 items-center px-6 py-4">
              <MapPin className="mr-4 h-5 w-5 text-zinc-400" />

              <div className="flex-1">
                <span className="mb-1 block text-[9px] font-bold tracking-wider text-zinc-400 uppercase">
                  Where?
                </span>

                <input
                  type="text"
                  placeholder="Current location..."
                  value={location}
                  onFocus={() => setActiveField("location")}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full bg-transparent text-lg font-medium text-zinc-900 placeholder:text-zinc-300 focus:outline-none"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                const activityNorm = activity
                  .trim()
                  .toLowerCase()
                  .replace(/\s+/g, " ");
                const category =
                  SUGGESTION_TO_CATEGORY[activityNorm] ??
                  (activityNorm
                    ? activityNorm.replace(/\s+/g, "_")
                    : undefined);
                const city = location.trim() || undefined;
                const query = new URLSearchParams();
                if (category) query.set("category", category);
                if (city) query.set("city", city);
                setIsNavigating(true);
                router.push(`/studios?${query.toString()}`);
              }}
              disabled={isNavigating}
              className="group flex min-w-[140px] items-center justify-center rounded-xl bg-zinc-900 px-8 py-4 text-white transition-all duration-300 hover:bg-teal-500 disabled:cursor-wait disabled:opacity-70"
            >
              {isNavigating ? (
                <>
                  <svg
                    className="h-5 w-5 animate-spin text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span className="ml-2 text-sm font-bold tracking-widest uppercase">
                    Searching…
                  </span>
                </>
              ) : (
                <>
                  <span className="mr-2 text-sm font-bold tracking-widest uppercase">
                    Search
                  </span>
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </>
              )}
            </button>

            <AnimatePresence>
              {activeField && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute top-full right-0 left-0 z-50 mt-4 overflow-hidden rounded-2xl border border-zinc-100 bg-white p-2 shadow-2xl"
                >
                  <div className="grid gap-2 md:grid-cols-2">
                    <div className="p-4">
                      <p className="mb-4 ml-2 text-[10px] font-black text-zinc-400 uppercase">
                        Suggested {activeField}
                      </p>

                      {suggestions[activeField].map((item) => (
                        <button
                          key={item}
                          onMouseDown={() => {
                            if (activeField === "activity") {
                              setActivity(item);
                            } else {
                              setLocation(item);
                            }

                            setActiveField(null);
                          }}
                          className="flex w-full items-center rounded-xl px-4 py-3 text-left text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-50 hover:text-zinc-900"
                        >
                          <Navigation className="mr-3 h-3 w-3 opacity-30" />

                          {item}
                        </button>
                      ))}
                    </div>

                    <div className="hidden rounded-xl bg-zinc-50 p-6 md:block">
                      <p className="mb-2 text-xs font-bold text-zinc-900">
                        Popular this month
                      </p>

                      <p className="text-xs leading-relaxed text-zinc-500">
                        Join 2,000+ people framing their morning routine in
                        Downtown.
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="mt-16 flex flex-wrap items-center justify-center gap-x-8 gap-y-4">
            <span className="text-[10px] font-black tracking-[0.3em] text-zinc-300 uppercase">
              Popular:
            </span>
            {["Reformer", "Boxing", "Hot Yoga", "Crossfit"].map((tag) => (
              <button
                key={tag}
                onClick={() => setActivity(tag)}
                className="group relative text-sm font-medium text-zinc-400 transition-colors hover:text-zinc-950"
              >
                {tag}
                <span className="absolute -bottom-1 left-0 h-px w-0 bg-teal-500 transition-all group-hover:w-full" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Лёгкий декор: на мобильном большой blur под меню даёт лаги при открытии overlay */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 h-full w-full -translate-x-1/2 -translate-y-1/2">
        <div className="absolute top-0 left-1/4 h-64 w-64 rounded-full bg-teal-50/30 opacity-50 blur-xl md:h-72 md:w-72" />
      </div>
    </>
  );
};
