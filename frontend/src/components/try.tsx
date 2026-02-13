"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

// Mock data - replace with actual API call
const MOCK_STUDIOS = [
  {
    id: 1,
    name: "Flow Yoga Dublin",
    type: "Yoga",
    location: "Dublin 2",
    rating: 4.9,
    reviews: 127,
    price: 18,
    image: "/yoga.webp",
    verified: true,
    nextClass: "Today 18:00",
    spotsLeft: 4,
    rotation: -3,
  },
  {
    id: 2,
    name: "Urban Dance Studio",
    type: "Dance",
    location: "Dublin 1",
    rating: 4.8,
    reviews: 89,
    price: 22,
    image: "/cont.webp",
    verified: true,
    nextClass: "Tomorrow 19:30",
    spotsLeft: 8,
    rotation: 2,
  },
  {
    id: 3,
    name: "Core Pilates",
    type: "Pilates",
    location: "Dublin 4",
    rating: 5.0,
    reviews: 203,
    price: 15,
    image: "/hip-hop.webp",
    verified: false,
    nextClass: "Today 17:00",
    spotsLeft: 2,
    rotation: -2,
  },
  {
    id: 4,
    name: "Zen Movement",
    type: "Yoga",
    location: "Dublin 6",
    rating: 4.7,
    reviews: 156,
    price: 20,
    image: "/yoga.webp",
    verified: true,
    nextClass: "Today 20:00",
    spotsLeft: 6,
    rotation: 4,
  },
  {
    id: 5,
    name: "Rhythm Dance Co",
    type: "Dance",
    location: "Dublin 8",
    rating: 4.9,
    reviews: 94,
    price: 25,
    image: "/cont.webp",
    verified: true,
    nextClass: "Tomorrow 18:00",
    spotsLeft: 5,
    rotation: -4,
  },
  {
    id: 6,
    name: "Stretch & Flex",
    type: "Stretching",
    location: "Dublin 2",
    rating: 4.6,
    reviews: 67,
    price: 12,
    image: "/hip-hop.webp",
    verified: false,
    nextClass: "Today 16:00",
    spotsLeft: 10,
    rotation: 3,
  },
];

const CATEGORIES = ["All", "Yoga", "Dance", "Pilates", "Stretching", "Barre"];
const LOCATIONS = [
  "All Locations",
  "Dublin 1",
  "Dublin 2",
  "Dublin 4",
  "Dublin 6",
  "Dublin 8",
];

export const StudiosSearchPage = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedLocation, setSelectedLocation] = useState("All Locations");
  const [savedStudios, setSavedStudios] = useState<number[]>([]);

  // Filter studios based on search and filters
  const filteredStudios = MOCK_STUDIOS.filter((studio) => {
    const matchesSearch = studio.name
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === "All" || studio.type === selectedCategory;
    const matchesLocation =
      selectedLocation === "All Locations" ||
      studio.location === selectedLocation;
    return matchesSearch && matchesCategory && matchesLocation;
  });

  const toggleSave = (studioId: number) => {
    setSavedStudios((prev) =>
      prev.includes(studioId)
        ? prev.filter((id) => id !== studioId)
        : [...prev, studioId],
    );
  };

  return (
    <div className="min-h-screen bg-zinc-50">
      {/* Hero Search Section - Sticky */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-zinc-100 shadow-sm"
      >
        <div className="container mx-auto px-4 py-6">
          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-6 text-center text-3xl font-bold tracking-tight text-zinc-900 md:text-4xl"
          >
            Find your{" "}
            <span className="font-serif italic bg-gradient-to-r from-teal-500 to-lime-400 bg-clip-text text-transparent">
              perfect moment
            </span>
          </motion.h1>

          {/* Search Bar */}
          <div className="mx-auto max-w-3xl">
            <div className="flex flex-col gap-3 sm:flex-row">
              {/* Search Input */}
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="Search studios, classes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg border border-zinc-200 bg-white px-5 py-3.5 pl-12 text-zinc-900 placeholder-zinc-400 outline-none transition-all focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
                />
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-xl">
                  🔍
                </div>
              </div>

              {/* Location Dropdown */}
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="rounded-lg border border-zinc-200 bg-white px-5 py-3.5 text-zinc-900 outline-none transition-all focus:border-teal-400 focus:ring-2 focus:ring-teal-100 sm:w-48"
              >
                {LOCATIONS.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
            </div>

            {/* Quick Filters */}
            <div className="mt-4 flex items-center gap-2 overflow-x-auto pb-2">
              <span className="text-sm text-zinc-500 whitespace-nowrap">
                Quick:
              </span>
              {["Today", "This Week", "Beginners"].map((filter) => (
                <button
                  key={filter}
                  className="whitespace-nowrap rounded-full border border-zinc-200 bg-white px-4 py-1.5 text-sm text-zinc-600 transition-all hover:border-teal-300 hover:bg-teal-50 hover:text-teal-700"
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Category Pills */}
      <div className="border-b border-zinc-100 bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex gap-2 overflow-x-auto pb-2">
            {CATEGORIES.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`whitespace-nowrap rounded-full px-5 py-2 text-sm font-medium transition-all ${
                  selectedCategory === category
                    ? "bg-teal-500 text-white shadow-md shadow-teal-200"
                    : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results Header */}
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-zinc-600">
            <span className="font-semibold text-zinc-900">
              {filteredStudios.length}
            </span>{" "}
            studios found
          </p>
          <select className="rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm text-zinc-700 outline-none focus:border-teal-400">
            <option>Recommended</option>
            <option>Rating (High to Low)</option>
            <option>Price (Low to High)</option>
            <option>Distance</option>
          </select>
        </div>
      </div>

      {/* Studios Grid - Polaroid Cards */}
      <div className="container mx-auto px-4 pb-20">
        <AnimatePresence mode="popLayout">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {filteredStudios.map((studio, index) => (
              <motion.div
                key={studio.id}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{
                  duration: 0.4,
                  delay: index * 0.05,
                  layout: { type: "spring", stiffness: 200, damping: 25 },
                }}
                style={{
                  rotate: studio.rotation,
                }}
                className="group relative"
              >
                {/* Polaroid Card */}
                <div className="overflow-hidden rounded-lg bg-white p-3 shadow-lg transition-all duration-300 hover:shadow-2xl hover:shadow-teal-500/10 hover:-translate-y-2">
                  {/* Image Container */}
                  <div className="relative aspect-[4/5] overflow-hidden rounded-lg bg-zinc-100">
                    <img
                      src={studio.image}
                      alt={studio.name}
                      className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                    />

                    {/* Verified Badge */}
                    {studio.verified && (
                      <div className="absolute left-3 top-3 flex items-center gap-1 rounded-full bg-teal-500 px-2.5 py-1 text-xs font-bold text-white shadow-lg">
                        ✓ Verified
                      </div>
                    )}

                    {/* Save Heart */}
                    <button
                      onClick={() => toggleSave(studio.id)}
                      className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-white/90 backdrop-blur-sm transition-all hover:scale-110 hover:bg-white"
                    >
                      <span
                        className={
                          savedStudios.includes(studio.id)
                            ? "text-red-500"
                            : "text-zinc-400"
                        }
                      >
                        {savedStudios.includes(studio.id) ? "❤️" : "🤍"}
                      </span>
                    </button>

                    {/* Spots Left Badge */}
                    {studio.spotsLeft <= 5 && (
                      <div className="absolute bottom-3 left-3 rounded-lg bg-amber-400 px-2.5 py-1 text-xs font-black uppercase tracking-wide text-zinc-900">
                        🔥 {studio.spotsLeft} spots left
                      </div>
                    )}

                    {/* Type Label */}
                    <div className="absolute bottom-3 right-3 rounded-lg bg-white/90 px-2.5 py-1 text-xs font-bold uppercase tracking-widest text-zinc-600 backdrop-blur-sm">
                      {studio.type}
                    </div>
                  </div>

                  {/* Card Info */}
                  <div className="mt-4 px-1">
                    {/* Studio Name */}
                    <h3 className="mb-1 text-xl font-bold text-zinc-900">
                      {studio.name}
                    </h3>

                    {/* Meta Info */}
                    <div className="mb-3 flex items-center gap-3 text-sm text-zinc-600">
                      <div className="flex items-center gap-1">
                        <span className="text-amber-400">⭐</span>
                        <span className="font-semibold text-zinc-900">
                          {studio.rating}
                        </span>
                        <span>({studio.reviews})</span>
                      </div>
                      <span>•</span>
                      <div className="flex items-center gap-1">
                        <span>📍</span>
                        <span>{studio.location}</span>
                      </div>
                    </div>

                    {/* Price & Next Class */}
                    <div className="flex items-center justify-between">
                      <div className="text-lg font-mono font-bold text-teal-600">
                        €{studio.price}/class
                      </div>
                      <div className="text-xs text-zinc-500">
                        {studio.nextClass}
                      </div>
                    </div>

                    {/* CTA Button */}
                    <button className="mt-4 w-full rounded-lg bg-zinc-900 py-3 font-semibold text-white transition-all hover:bg-zinc-800">
                      View Details
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>

        {/* Empty State */}
        {filteredStudios.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="py-20 text-center"
          >
            <div className="mb-4 text-6xl">🔍</div>
            <h3 className="mb-2 text-2xl font-semibold text-zinc-900">
              No studios found
            </h3>
            <p className="mb-6 text-zinc-600">
              Try adjusting your filters or search in a different area
            </p>
            <button
              onClick={() => {
                setSearchQuery("");
                setSelectedCategory("All");
                setSelectedLocation("All Locations");
              }}
              className="rounded-lg bg-teal-500 px-6 py-3 font-semibold text-white transition-all hover:bg-teal-600"
            >
              Clear Filters
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
};
