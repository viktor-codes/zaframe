"use client";
import { motion, useInView, AnimatePresence } from "framer-motion";
import { useRef, useState, useEffect } from "react";
import {
  Search,
  ArrowRight,
  MapPin,
  Navigation,
  Clock,
  Star,
} from "lucide-react";

export const SearchSection = () => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-20%" });

  const [activity, setActivity] = useState("");
  const [location, setLocation] = useState("");
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

  const quickFilters = [
    { label: "Today", icon: <Clock className="w-3 h-3" /> },
    { label: "This Week", icon: <Clock className="w-3 h-3" /> },
    { label: "Beginners", icon: <Star className="w-3 h-3" /> },
  ];

  return (
    <section
      ref={ref}
      className="relative bg-white py-32 md:py-48 overflow-hidden"
    >
      <div className="container relative z-10 mx-auto px-6 max-w-6xl">
        <div className="flex flex-col items-center">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            className="text-[10px] font-black uppercase tracking-[0.4em] text-zinc-400 mb-12"
          >
            Find your next practice
          </motion.span>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            className="w-full relative"
          >
            {/* Main Search Bar Container */}
            <div className="relative flex flex-col md:flex-row items-stretch bg-zinc-50 rounded-2xl p-2 border border-zinc-100 shadow-sm focus-within:shadow-xl focus-within:bg-white transition-all duration-500">
              {/* Activity Input */}
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

              {/* Location Input */}
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

              {/* Submit Button */}
              <button className="bg-zinc-900 hover:bg-teal-500 text-white rounded-xl px-8 py-4 flex items-center justify-center transition-all duration-300 group">
                <span className="mr-2 font-bold text-sm uppercase tracking-widest">
                  Search
                </span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>

              {/* Autocomplete Suggestions Dropdown */}
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

            {/* Quick Filters */}
            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <div className="flex items-center gap-2 mr-4 border-r border-zinc-100 pr-4">
                <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                  Filters:
                </span>
              </div>
              {quickFilters.map((filter) => (
                <button
                  key={filter.label}
                  className="flex items-center gap-2 px-5 py-2 rounded-full bg-white border border-zinc-100 text-xs font-bold text-zinc-500 hover:border-teal-500 hover:text-teal-600 transition-all shadow-sm hover:shadow-md"
                >
                  {filter.icon}
                  {filter.label}
                </button>
              ))}
            </div>

            {/* Popular Searches Tags */}
            <div className="mt-12 text-center">
              <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.2em] mb-4">
                Popular Searches
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {["Reformer", "Boxing", "Hot Yoga", "Barre", "Crossfit"].map(
                  (tag) => (
                    <button
                      key={tag}
                      onClick={() => setActivity(tag)}
                      className="text-sm font-serif italic text-zinc-400 hover:text-zinc-900 transition-colors px-2"
                    >
                      #{tag}
                    </button>
                  ),
                )}
              </div>
            </div>
          </motion.div>

          {/* Overlay to close suggestions */}
          {activeField && (
            <div
              className="fixed inset-0 z-40"
              onClick={() => setActiveField(null)}
            />
          )}
        </div>
      </div>
    </section>
  );
};
