"use client";

import { motion, useInView, AnimatePresence } from "framer-motion";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, ArrowRight, MapPin, Navigation } from "lucide-react";
import { SectionHeading } from "@/components/SectionHeading";

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
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-20%" });

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
      <div ref={ref} className="container relative z-10 mx-auto px-6 max-w-5xl">
        <div className="text-left md:text-center mb-20 md:mb-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            <SectionHeading
              size="section"
              as="h2"
              className="text-zinc-900 leading-[0.9]"
            >
              Ready to find <br />
              <span className="font-serif italic font-light text-zinc-400">
                your frame?
              </span>
            </SectionHeading>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="w-full relative"
        >
          <div className="relative flex flex-col md:flex-row items-stretch bg-zinc-50 rounded-2xl p-2 border border-zinc-100 shadow-sm focus-within:shadow-xl focus-within:bg-white transition-all duration-500">
            <div className="flex-1 relative flex items-center px-6 py-4 border-b md:border-b-0 md:border-r border-zinc-200/50">
              <Search className="w-5 h-5 text-zinc-400 mr-4" />

              <div className="flex-1">
                <span className="block text-[9px] font-bold uppercase tracking-wider text-zinc-400 mb-1">
                  What to do?
                </span>

                <input
                  type="text"
                  placeholder="Yoga, Boxing, Dance..."
                  value={activity}
                  onFocus={() => setActiveField("activity")}
                  onChange={(e) => setActivity(e.target.value)}
                  className="w-full bg-transparent text-lg font-medium text-zinc-900 focus:outline-none placeholder:text-zinc-300"
                />
              </div>
            </div>

            <div className="flex-1 relative flex items-center px-6 py-4">
              <MapPin className="w-5 h-5 text-zinc-400 mr-4" />

              <div className="flex-1">
                <span className="block text-[9px] font-bold uppercase tracking-wider text-zinc-400 mb-1">
                  Where?
                </span>

                <input
                  type="text"
                  placeholder="Current location..."
                  value={location}
                  onFocus={() => setActiveField("location")}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full bg-transparent text-lg font-medium text-zinc-900 focus:outline-none placeholder:text-zinc-300"
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
              className="bg-zinc-900 hover:bg-teal-500 text-white rounded-xl px-8 py-4 flex items-center justify-center transition-all duration-300 group disabled:opacity-70 disabled:cursor-wait min-w-[140px]"
            >
              {isNavigating ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5 text-white"
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
                  <span className="ml-2 font-bold text-sm uppercase tracking-widest">
                    Searching…
                  </span>
                </>
              ) : (
                <>
                  <span className="mr-2 font-bold text-sm uppercase tracking-widest">
                    Search
                  </span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>

            <AnimatePresence>
              {activeField && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute top-full left-0 right-0 mt-4 bg-white rounded-2xl border border-zinc-100 shadow-2xl z-50 overflow-hidden p-2"
                >
                  <div className="grid md:grid-cols-2 gap-2">
                    <div className="p-4">
                      <p className="text-[10px] font-black uppercase text-zinc-400 mb-4 ml-2">
                        Suggested {activeField}
                      </p>

                      {suggestions[activeField].map((item) => (
                        <button
                          key={item}
                          onMouseDown={() => {
                            activeField === "activity"
                              ? setActivity(item)
                              : setLocation(item);

                            setActiveField(null);
                          }}
                          className="w-full text-left px-4 py-3 rounded-xl hover:bg-zinc-50 text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors flex items-center"
                        >
                          <Navigation className="w-3 h-3 mr-3 opacity-30" />

                          {item}
                        </button>
                      ))}
                    </div>

                    <div className="hidden md:block bg-zinc-50 rounded-xl p-6">
                      <p className="text-xs font-bold text-zinc-900 mb-2">
                        Popular this month
                      </p>

                      <p className="text-xs text-zinc-500 leading-relaxed">
                        Join 2,000+ people framing their morning routine in
                        Downtown.
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="mt-16 flex flex-wrap justify-center items-center gap-x-8 gap-y-4">
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-300">
              Popular:
            </span>
            {["Reformer", "Boxing", "Hot Yoga", "Crossfit"].map((tag) => (
              <button
                key={tag}
                onClick={() => setActivity(tag)}
                className="text-sm font-medium text-zinc-400 hover:text-zinc-950 transition-colors relative group"
              >
                {tag}
                <span className="absolute -bottom-1 left-0 w-0 h-px bg-teal-500 transition-all group-hover:w-full" />
              </button>
            ))}
          </div>
        </motion.div>
      </div>

      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-teal-50/30 blur-[120px] rounded-full opacity-50" />
      </div>
    </>
  );
}
