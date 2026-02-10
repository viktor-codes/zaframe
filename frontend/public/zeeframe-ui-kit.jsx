import React, { useState } from "react";

// ==========================================
// DESIGN SYSTEM TOKENS
// ==========================================

const tokens = {
  colors: {
    brand: {
      gradient: "bg-gradient-to-br from-sky-400 via-teal-400 to-lime-300",
      blue: "#0EA5E9",
      teal: "#2DD4BF",
      lime: "#BEF264",
    },
    neutral: {
      50: "#FAFAFA",
      100: "#F5F5F5",
      200: "#E5E5E5",
      300: "#D4D4D4",
      600: "#52525B",
      900: "#18181B",
    },
    status: {
      success: "#10B981",
      warning: "#F59E0B",
      danger: "#EF4444",
    },
  },
  shadows: {
    paper:
      "shadow-[0_18px_45px_rgba(16,17,20,0.14)] hover:shadow-[0_26px_70px_rgba(16,17,20,0.18)]",
    hover: "shadow-[0_26px_70px_rgba(16,17,20,0.18)]",
    lift: "shadow-[0_40px_100px_rgba(16,17,20,0.22)]",
    modal: "shadow-[0_60px_140px_rgba(16,17,20,0.35)]",
  },
  radius: {
    sm: "12px",
    md: "16px",
    lg: "18px",
    xl: "24px",
    xxl: "32px",
    full: "999px",
  },
};

// ==========================================
// BASE COMPONENTS
// ==========================================

// Button Component
function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  ...props
}) {
  const base =
    "inline-flex items-center justify-center rounded-full font-semibold transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed";

  const variants = {
    primary: `bg-gradient-to-br from-sky-400 via-teal-400 to-lime-300 text-zinc-900 shadow-sm hover:shadow-md hover:brightness-[1.03]`,
    secondary:
      "bg-white text-zinc-900 border-2 border-zinc-200 hover:bg-zinc-50 hover:border-zinc-300",
    ghost:
      "bg-transparent text-zinc-800 hover:bg-zinc-100 active:bg-zinc-200",
    danger:
      "bg-red-500 text-white hover:bg-red-600 shadow-sm hover:shadow-md",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

// Chip Component
function Chip({
  children,
  tone = "neutral",
  size = "sm",
  className = "",
}) {
  const tones = {
    neutral: "bg-white/85 text-zinc-900 border border-black/10",
    brand: "bg-gradient-to-br from-sky-50 to-teal-50 text-zinc-900 border border-teal-200/50",
    success: "bg-emerald-50 text-emerald-900 border border-emerald-200",
    warning: "bg-amber-50 text-amber-900 border border-amber-200",
    danger: "bg-red-50 text-red-900 border border-red-200",
  };

  const sizes = {
    xs: "px-2 py-0.5 text-[10px]",
    sm: "px-3 py-1 text-xs",
    md: "px-4 py-1.5 text-sm",
  };

  return (
    <div
      className={`inline-flex items-center rounded-full font-semibold backdrop-blur ${tones[tone]} ${sizes[size]} ${className}`}
    >
      {children}
    </div>
  );
}

// Badge Component
function Badge({ children, variant = "default" }) {
  const variants = {
    default: "bg-zinc-100 text-zinc-800",
    verified: "bg-gradient-to-br from-sky-50 to-teal-50 text-teal-700 border border-teal-200",
    new: "bg-gradient-to-br from-lime-50 to-yellow-50 text-lime-700 border border-lime-200",
  };

  return (
    <div
      className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-wide ${variants[variant]}`}
    >
      {variant === "verified" && "✓"}
      {children}
    </div>
  );
}

// Input Component
function Input({ label, helper, error, className = "", ...props }) {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-2 block text-sm font-semibold text-zinc-700">
          {label}
        </label>
      )}
      <input
        className={`w-full rounded-2xl border-2 border-zinc-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-teal-400 focus:ring-4 focus:ring-teal-100 disabled:bg-zinc-50 ${
          error ? "border-red-300 focus:border-red-400 focus:ring-red-100" : ""
        } ${className}`}
        {...props}
      />
      {helper && !error && (
        <p className="mt-1 text-xs text-zinc-500">{helper}</p>
      )}
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

// Search Bar Component
function SearchBar({ onSearch }) {
  return (
    <div className="flex w-full max-w-[800px] items-center gap-2 rounded-full border border-zinc-200 bg-white px-4 py-3 shadow-sm transition hover:shadow-md">
      <input
        placeholder="City or studio"
        className="w-full bg-transparent text-sm outline-none placeholder:text-zinc-400"
      />
      <div className="hidden h-6 w-px bg-zinc-200 md:block" />
      <input
        type="date"
        placeholder="Date"
        className="hidden w-[140px] bg-transparent text-sm outline-none placeholder:text-zinc-400 md:block"
      />
      <div className="hidden h-6 w-px bg-zinc-200 md:block" />
      <input
        placeholder="Yoga, dance, pilates..."
        className="hidden w-[160px] bg-transparent text-sm outline-none placeholder:text-zinc-400 md:block"
      />
      <Button onClick={onSearch}>Search</Button>
    </div>
  );
}

// ==========================================
// POLAROID CARD SYSTEM
// ==========================================

// Base Polaroid Card
function PolaroidCard({
  image,
  children,
  caption,
  className = "",
  topRight,
  topLeft,
  bottomContent,
  onClick,
  size = "md",
}) {
  const sizes = {
    sm: "max-w-[280px]",
    md: "max-w-[360px]",
    lg: "max-w-[440px]",
  };

  const imageSizes = {
    sm: "h-[200px]",
    md: "h-[240px]",
    lg: "h-[320px]",
  };

  return (
    <div
      onClick={onClick}
      className={`group relative w-full ${sizes[size]} cursor-pointer rounded-[24px] bg-white shadow-[0_18px_45px_rgba(16,17,20,0.14)] transition-all duration-300 hover:-translate-y-2 hover:shadow-[0_26px_70px_rgba(16,17,20,0.18)] ${className}`}
    >
      {/* Photo area */}
      <div className="relative p-4 pb-3">
        <div className="relative overflow-hidden rounded-[18px]">
          <img
            src={image}
            alt=""
            className={`${imageSizes[size]} w-full object-cover transition duration-500 group-hover:scale-[1.03]`}
          />

          {/* Overlays */}
          <div className="absolute left-3 top-3 flex flex-wrap gap-2">
            {topLeft}
          </div>
          <div className="absolute right-3 top-3 flex flex-wrap gap-2">
            {topRight}
          </div>

          {/* Gradient overlay */}
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent" />
        </div>
      </div>

      {/* Caption area */}
      <div className="px-5 pb-5">
        <div className="min-h-[60px]">
          {caption && (
            <div className="text-[17px] font-bold tracking-tight text-zinc-900">
              {caption}
            </div>
          )}
          {children && (
            <div className="mt-1 text-sm text-zinc-600">{children}</div>
          )}
        </div>

        {bottomContent && <div className="mt-4">{bottomContent}</div>}
      </div>
    </div>
  );
}

// Studio Card
function StudioCard({
  image,
  name,
  location,
  tags = [],
  rating = 4.9,
  distance = "8 min",
  verified = true,
  onBook,
}) {
  return (
    <PolaroidCard
      image={image}
      caption={name}
      topLeft={
        <>
          <Chip tone="neutral">⭐ {rating}</Chip>
          <Chip tone="neutral">🚶 {distance}</Chip>
        </>
      }
      topRight={verified && <Badge variant="verified">Verified</Badge>}
      bottomContent={
        <>
          <div className="text-sm text-zinc-600">{location}</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {tags.slice(0, 3).map((tag, i) => (
              <Chip key={i} size="xs">
                {tag}
              </Chip>
            ))}
          </div>
          <div className="mt-4 flex gap-2">
            <Button className="flex-1" onClick={onBook}>
              Book
            </Button>
            <Button variant="secondary" className="flex-1">
              Schedule
            </Button>
          </div>
        </>
      }
    />
  );
}

// Class Card
function ClassCard({
  image,
  title,
  studio,
  instructor,
  time,
  duration = "60 min",
  price = "$18",
  spotsLeft,
  level = "All levels",
  onBook,
}) {
  return (
    <PolaroidCard
      image={image}
      caption={title}
      topLeft={
        <>
          <Chip tone="neutral">🕐 {time}</Chip>
          <Chip tone="neutral">{duration}</Chip>
        </>
      }
      topRight={
        spotsLeft !== undefined && spotsLeft <= 5 ? (
          <Chip tone="warning">⚡ {spotsLeft} spots</Chip>
        ) : (
          <Chip tone="brand">{price}</Chip>
        )
      }
      bottomContent={
        <>
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-zinc-700">{studio}</span>
            <span className="text-zinc-500">{level}</span>
          </div>
          {instructor && (
            <div className="mt-1 text-xs text-zinc-500">
              with {instructor}
            </div>
          )}
          <div className="mt-4">
            <Button className="w-full" onClick={onBook}>
              Book this class
            </Button>
          </div>
        </>
      }
    />
  );
}

// Instructor Card
function InstructorCard({
  image,
  name,
  specialties = [],
  rating = 4.9,
  classes = 120,
  bio,
}) {
  return (
    <PolaroidCard
      image={image}
      caption={name}
      size="sm"
      topRight={<Chip tone="neutral">⭐ {rating}</Chip>}
      bottomContent={
        <>
          <div className="flex flex-wrap gap-2">
            {specialties.slice(0, 2).map((s, i) => (
              <Chip key={i} size="xs" tone="brand">
                {s}
              </Chip>
            ))}
          </div>
          {bio && (
            <p className="mt-2 text-xs leading-relaxed text-zinc-600">
              {bio}
            </p>
          )}
          <div className="mt-3 text-xs text-zinc-500">{classes} classes taught</div>
        </>
      }
    />
  );
}

// Review Card
function ReviewCard({ author, rating, date, text, image }) {
  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <img
          src={image}
          alt={author}
          className="h-12 w-12 rounded-full object-cover"
        />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <div className="font-semibold text-zinc-900">{author}</div>
            <div className="flex items-center gap-1 text-sm">
              <span>⭐</span>
              <span className="font-semibold">{rating}</span>
            </div>
          </div>
          <div className="text-xs text-zinc-500">{date}</div>
          <p className="mt-2 text-sm leading-relaxed text-zinc-700">{text}</p>
        </div>
      </div>
    </div>
  );
}

// Schedule Slot
function ScheduleSlot({
  time,
  title,
  instructor,
  duration,
  price,
  spotsLeft,
  onBook,
}) {
  return (
    <div className="group flex items-center justify-between rounded-2xl border border-zinc-200 bg-white p-4 transition hover:border-teal-300 hover:bg-teal-50/30">
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <div className="text-lg font-bold text-zinc-900">{time}</div>
          <div className="h-4 w-px bg-zinc-300" />
          <div className="font-semibold text-zinc-800">{title}</div>
          {spotsLeft <= 5 && (
            <Chip tone="warning" size="xs">
              {spotsLeft} left
            </Chip>
          )}
        </div>
        <div className="mt-1 flex items-center gap-4 text-xs text-zinc-600">
          <span>{instructor}</span>
          <span>•</span>
          <span>{duration}</span>
          <span>•</span>
          <span className="font-semibold text-zinc-900">{price}</span>
        </div>
      </div>
      <Button size="sm" onClick={onBook}>
        Book
      </Button>
    </div>
  );
}

// Booking Summary Card
function BookingSummaryCard({ studio, classType, date, time, price, credits }) {
  return (
    <div className="rounded-2xl border-2 border-zinc-200 bg-zinc-50 p-6">
      <div className="mb-4 text-sm font-semibold uppercase tracking-wide text-zinc-500">
        Booking Summary
      </div>
      
      <div className="space-y-3">
        <div>
          <div className="text-xs text-zinc-500">Studio</div>
          <div className="font-semibold text-zinc-900">{studio}</div>
        </div>
        
        <div>
          <div className="text-xs text-zinc-500">Class</div>
          <div className="font-semibold text-zinc-900">{classType}</div>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-xs text-zinc-500">Date</div>
            <div className="font-semibold text-zinc-900">{date}</div>
          </div>
          <div>
            <div className="text-xs text-zinc-500">Time</div>
            <div className="font-semibold text-zinc-900">{time}</div>
          </div>
        </div>
      </div>

      <div className="my-4 border-t border-zinc-300" />

      <div className="flex items-center justify-between">
        <div className="text-sm text-zinc-600">Total</div>
        <div className="text-xl font-bold text-zinc-900">{price}</div>
      </div>

      {credits && (
        <div className="mt-2 rounded-lg bg-gradient-to-br from-sky-50 to-teal-50 p-3 text-xs">
          <span className="font-semibold text-teal-700">
            💎 Use 1 credit instead
          </span>
        </div>
      )}
    </div>
  );
}

// ==========================================
// MODAL SYSTEM
// ==========================================

function PolaroidModal({ isOpen, onClose, title, children, size = "md" }) {
  if (!isOpen) return null;

  const sizes = {
    sm: "max-w-md",
    md: "max-w-2xl",
    lg: "max-w-4xl",
    xl: "max-w-6xl",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`relative w-full ${sizes[size]} rounded-[32px] bg-white p-8 shadow-[0_60px_140px_rgba(16,17,20,0.35)] animate-in fade-in zoom-in-95 duration-300`}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-6 top-6 flex h-10 w-10 items-center justify-center rounded-full bg-zinc-100 text-zinc-600 transition hover:bg-zinc-200 hover:text-zinc-900"
        >
          ✕
        </button>

        {/* Title */}
        {title && (
          <div className="mb-6 text-2xl font-bold tracking-tight text-zinc-900">
            {title}
          </div>
        )}

        {/* Content */}
        <div>{children}</div>
      </div>
    </div>
  );
}

// ==========================================
// COMPLEX COMPONENTS
// ==========================================

// Polaroid Stack (carousel)
function PolaroidStack({ cards = [] }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  return (
    <div className="relative w-full">
      <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
        {cards.map((card, index) => (
          <div key={index} className="flex-shrink-0">
            {card}
          </div>
        ))}
      </div>
    </div>
  );
}

// Tabs Component
function Tabs({ tabs, activeTab, onChange }) {
  return (
    <div className="flex gap-2 border-b border-zinc-200">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`relative px-4 py-3 text-sm font-semibold transition ${
            activeTab === tab.id
              ? "text-zinc-900"
              : "text-zinc-500 hover:text-zinc-700"
          }`}
        >
          {tab.label}
          {activeTab === tab.id && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-sky-400 via-teal-400 to-lime-300" />
          )}
        </button>
      ))}
    </div>
  );
}

// Toast Notification
function Toast({ message, type = "success", onClose }) {
  const types = {
    success: "bg-emerald-500 text-white",
    warning: "bg-amber-500 text-white",
    danger: "bg-red-500 text-white",
    info: "bg-sky-500 text-white",
  };

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl px-5 py-3 shadow-lg animate-in slide-in-from-bottom duration-300 ${types[type]}`}
    >
      <span className="text-sm font-semibold">{message}</span>
      <button
        onClick={onClose}
        className="ml-2 opacity-80 hover:opacity-100"
      >
        ✕
      </button>
    </div>
  );
}

// ==========================================
// PAGE COMPONENTS
// ==========================================

// Navigation Bar
function NavigationBar() {
  return (
    <nav className="fixed left-0 right-0 top-0 z-40 border-b border-zinc-200 bg-white/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 via-teal-400 to-lime-300">
            <span className="text-lg font-bold text-zinc-900">Z</span>
          </div>
          <span className="text-xl font-bold tracking-tight text-zinc-900">
            ZeeFrame
          </span>
        </div>

        {/* Search (desktop) */}
        <div className="hidden md:block">
          <SearchBar />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm">
            Saved
          </Button>
          <Button variant="ghost" size="sm">
            Bookings
          </Button>
          <button className="flex h-10 w-10 items-center justify-center rounded-full bg-zinc-100">
            <span className="text-sm font-semibold">👤</span>
          </button>
        </div>
      </div>
    </nav>
  );
}

// Hero Section
function HeroSection() {
  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-zinc-50 via-white to-teal-50/30 px-6 pb-20 pt-32">
      {/* Decorative elements */}
      <div className="absolute right-0 top-0 h-[400px] w-[400px] rounded-full bg-gradient-to-br from-sky-200/20 via-teal-200/20 to-lime-200/20 blur-3xl" />
      
      <div className="relative mx-auto max-w-4xl text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-4 py-2 text-sm font-semibold text-teal-700">
          <span>📸</span>
          <span>Book it like a moment</span>
        </div>
        
        <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight text-zinc-900 md:text-6xl">
          Premium booking for<br />
          <span className="bg-gradient-to-r from-sky-500 via-teal-500 to-lime-500 bg-clip-text text-transparent">
            yoga, dance & movement
          </span>
        </h1>
        
        <p className="mx-auto mb-10 max-w-2xl text-lg text-zinc-600">
          Discover and book classes at verified studios. Every session is a
          moment worth capturing.
        </p>
        
        <div className="flex flex-col items-center gap-4">
          <SearchBar />
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-zinc-500">
            <span>Popular:</span>
            <Chip size="xs">Vinyasa Yoga</Chip>
            <Chip size="xs">Contemporary Dance</Chip>
            <Chip size="xs">Pilates</Chip>
          </div>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// DEMO SCREENS
// ==========================================

function DemoHome() {
  const [activeTab, setActiveTab] = useState("recommended");

  const sampleStudios = [
    {
      image: "https://images.unsplash.com/photo-1554311884-415bfda6f5e3?w=800&auto=format&fit=crop&q=80",
      name: "Flow House Studio",
      location: "Downtown • 0.8 km",
      tags: ["Yoga", "Pilates", "Breathwork"],
      rating: 4.9,
      distance: "8 min",
    },
    {
      image: "https://images.unsplash.com/photo-1599447421416-3414500d18a5?w=800&auto=format&fit=crop&q=80",
      name: "ZeeDance Lab",
      location: "Riverside • 1.6 km",
      tags: ["Dance", "Stretch", "Contemporary"],
      rating: 4.8,
      distance: "12 min",
    },
    {
      image: "https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=800&auto=format&fit=crop&q=80",
      name: "Mindful Movement Co",
      location: "West End • 2.1 km",
      tags: ["Yoga", "Meditation", "Wellness"],
      rating: 4.9,
      distance: "15 min",
    },
  ];

  const sampleClasses = [
    {
      image: "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800&auto=format&fit=crop&q=80",
      title: "Vinyasa Flow",
      studio: "Flow House Studio",
      instructor: "Sarah Chen",
      time: "19:00",
      duration: "60 min",
      price: "$18",
      spotsLeft: 3,
      level: "Intermediate",
    },
    {
      image: "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800&auto=format&fit=crop&q=80",
      title: "Contemporary Fusion",
      studio: "ZeeDance Lab",
      instructor: "Marcus Rivera",
      time: "18:30",
      duration: "75 min",
      price: "$22",
      level: "All levels",
    },
    {
      image: "https://images.unsplash.com/photo-1603988363607-e1e4a66962c6?w=800&auto=format&fit=crop&q=80",
      title: "Restorative Yoga",
      studio: "Mindful Movement Co",
      instructor: "Luna Park",
      time: "20:00",
      duration: "90 min",
      price: "$20",
      level: "Beginner",
    },
  ];

  return (
    <div className="min-h-screen bg-zinc-50">
      <NavigationBar />
      <HeroSection />

      {/* Recommended section */}
      <section className="mx-auto max-w-7xl px-6 py-12">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold tracking-tight text-zinc-900">
            ✨ Recommended for you
          </h2>
          <Button variant="ghost" size="sm">
            See all →
          </Button>
        </div>

        <PolaroidStack
          cards={sampleStudios.map((studio, i) => (
            <StudioCard key={i} {...studio} />
          ))}
        />
      </section>

      {/* This week section */}
      <section className="mx-auto max-w-7xl px-6 py-12">
        <div className="mb-6">
          <h2 className="mb-2 text-2xl font-bold tracking-tight text-zinc-900">
            📅 This week
          </h2>
          <p className="text-zinc-600">
            Classes happening in the next 7 days
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {sampleClasses.map((cls, i) => (
            <ClassCard key={i} {...cls} />
          ))}
        </div>
      </section>

      {/* Featured studios */}
      <section className="bg-white py-16">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-8 text-center">
            <h2 className="mb-2 text-2xl font-bold tracking-tight text-zinc-900">
              🏆 Featured Studios
            </h2>
            <p className="text-zinc-600">
              Verified spaces for your practice
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {sampleStudios.map((studio, i) => (
              <StudioCard key={i} {...studio} />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function DemoStudioDetail() {
  const [activeTab, setActiveTab] = useState("schedule");
  const [selectedDay, setSelectedDay] = useState("Mon");

  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  const scheduleSlots = [
    {
      time: "07:00",
      title: "Morning Flow",
      instructor: "Sarah Chen",
      duration: "60 min",
      price: "$18",
      spotsLeft: 8,
    },
    {
      time: "09:30",
      title: "Power Vinyasa",
      instructor: "Marcus Rivera",
      duration: "75 min",
      price: "$22",
      spotsLeft: 3,
    },
    {
      time: "12:00",
      title: "Lunch Break Yoga",
      instructor: "Luna Park",
      duration: "45 min",
      price: "$15",
      spotsLeft: 12,
    },
    {
      time: "18:00",
      title: "Evening Flow",
      instructor: "Sarah Chen",
      duration: "60 min",
      price: "$18",
      spotsLeft: 2,
    },
  ];

  return (
    <div className="min-h-screen bg-zinc-50">
      <NavigationBar />

      <div className="mx-auto max-w-7xl px-6 py-24">
        {/* Studio hero */}
        <div className="mb-8">
          <PolaroidCard
            image="https://images.unsplash.com/photo-1554311884-415bfda6f5e3?w=1200&auto=format&fit=crop&q=80"
            size="lg"
            topLeft={
              <>
                <Chip tone="neutral">⭐ 4.9 (234 reviews)</Chip>
                <Chip tone="neutral">🚶 8 min</Chip>
              </>
            }
            topRight={<Badge variant="verified">Verified</Badge>}
          />

          <div className="mt-6">
            <h1 className="mb-2 text-3xl font-bold tracking-tight text-zinc-900">
              Flow House Studio
            </h1>
            <p className="text-zinc-600">
              📍 Downtown • 123 Wellness Street • Open 7am - 9pm
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Chip>Yoga</Chip>
              <Chip>Pilates</Chip>
              <Chip>Breathwork</Chip>
              <Chip>Meditation</Chip>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs
          tabs={[
            { id: "schedule", label: "Schedule" },
            { id: "about", label: "About" },
            { id: "reviews", label: "Reviews" },
          ]}
          activeTab={activeTab}
          onChange={setActiveTab}
        />

        {/* Schedule tab content */}
        {activeTab === "schedule" && (
          <div className="mt-6">
            {/* Day selector */}
            <div className="mb-6 flex gap-2 overflow-x-auto pb-2">
              {days.map((day) => (
                <button
                  key={day}
                  onClick={() => setSelectedDay(day)}
                  className={`flex-shrink-0 rounded-full px-5 py-2 text-sm font-semibold transition ${
                    selectedDay === day
                      ? "bg-gradient-to-br from-sky-400 via-teal-400 to-lime-300 text-zinc-900"
                      : "bg-white text-zinc-600 hover:bg-zinc-100"
                  }`}
                >
                  {day}
                </button>
              ))}
            </div>

            {/* Schedule slots */}
            <div className="space-y-3">
              {scheduleSlots.map((slot, i) => (
                <ScheduleSlot key={i} {...slot} />
              ))}
            </div>
          </div>
        )}

        {/* About tab content */}
        {activeTab === "about" && (
          <div className="mt-6 space-y-6">
            <div className="rounded-2xl bg-white p-6">
              <h3 className="mb-3 font-bold text-zinc-900">About</h3>
              <p className="leading-relaxed text-zinc-600">
                Flow House Studio is a premium wellness space offering yoga,
                pilates, and mindful movement classes. Our experienced
                instructors create transformative experiences in a beautiful,
                light-filled environment. Every session is designed to help you
                connect with your practice and community.
              </p>
            </div>

            <div className="rounded-2xl bg-white p-6">
              <h3 className="mb-3 font-bold text-zinc-900">Amenities</h3>
              <div className="grid grid-cols-2 gap-3 text-sm text-zinc-600">
                <div>✓ Showers & lockers</div>
                <div>✓ Mat rental</div>
                <div>✓ Filtered water</div>
                <div>✓ Towel service</div>
                <div>✓ Props provided</div>
                <div>✓ Retail shop</div>
              </div>
            </div>
          </div>
        )}

        {/* Reviews tab content */}
        {activeTab === "reviews" && (
          <div className="mt-6 space-y-4">
            <ReviewCard
              author="Emma Wilson"
              rating={5.0}
              date="2 days ago"
              image="https://i.pravatar.cc/150?img=1"
              text="Absolutely love this studio! The instructors are incredible and the space is beautiful. The polaroid-style booking system makes it feel so special."
            />
            <ReviewCard
              author="James Chen"
              rating={4.8}
              date="1 week ago"
              image="https://i.pravatar.cc/150?img=2"
              text="Great classes and convenient location. The app makes booking super easy. Would recommend to anyone looking for a solid yoga practice."
            />
            <ReviewCard
              author="Sofia Martinez"
              rating={5.0}
              date="2 weeks ago"
              image="https://i.pravatar.cc/150?img=3"
              text="This is my favorite studio in the city. Every class feels like a special moment worth capturing. The community here is amazing!"
            />
          </div>
        )}
      </div>
    </div>
  );
}

function DemoBookingFlow() {
  const [modalOpen, setModalOpen] = useState(true);
  const [bookingStep, setBookingStep] = useState(1);

  return (
    <div className="min-h-screen bg-zinc-50">
      <NavigationBar />

      <PolaroidModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Book: Vinyasa Flow"
        size="lg"
      >
        {/* Step indicator */}
        <div className="mb-8 flex items-center justify-between">
          {[1, 2, 3].map((step) => (
            <React.Fragment key={step}>
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full font-semibold ${
                  step === bookingStep
                    ? "bg-gradient-to-br from-sky-400 via-teal-400 to-lime-300 text-zinc-900"
                    : step < bookingStep
                    ? "bg-teal-500 text-white"
                    : "bg-zinc-200 text-zinc-500"
                }`}
              >
                {step < bookingStep ? "✓" : step}
              </div>
              {step < 3 && (
                <div
                  className={`h-1 flex-1 ${
                    step < bookingStep ? "bg-teal-500" : "bg-zinc-200"
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Step 1: Select time */}
        {bookingStep === 1 && (
          <div>
            <h3 className="mb-4 text-lg font-bold">Select date & time</h3>
            <div className="mb-6 grid grid-cols-7 gap-2">
              {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => (
                <button
                  key={day}
                  className="rounded-xl border-2 border-zinc-200 bg-white p-3 text-center text-sm font-semibold hover:border-teal-400"
                >
                  <div className="text-xs text-zinc-500">{day}</div>
                  <div className="mt-1 text-lg">12</div>
                </button>
              ))}
            </div>

            <div className="space-y-2">
              {["18:00", "19:00", "20:00"].map((time) => (
                <button
                  key={time}
                  className="w-full rounded-xl border-2 border-zinc-200 bg-white p-4 text-left font-semibold transition hover:border-teal-400 hover:bg-teal-50/30"
                >
                  {time} • 60 min • $18
                </button>
              ))}
            </div>

            <div className="mt-6 flex gap-3">
              <Button variant="secondary" className="flex-1" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <Button className="flex-1" onClick={() => setBookingStep(2)}>
                Continue
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Choose plan */}
        {bookingStep === 2 && (
          <div>
            <h3 className="mb-4 text-lg font-bold">Choose payment method</h3>
            <div className="space-y-3">
              <button className="w-full rounded-2xl border-2 border-teal-400 bg-gradient-to-br from-teal-50 to-sky-50 p-6 text-left transition hover:shadow-md">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold">Use 1 credit</div>
                    <div className="text-sm text-zinc-600">
                      You have 8 credits remaining
                    </div>
                  </div>
                  <div className="text-2xl">💎</div>
                </div>
              </button>

              <button className="w-full rounded-2xl border-2 border-zinc-200 bg-white p-6 text-left transition hover:border-zinc-300">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold">Pay $18</div>
                    <div className="text-sm text-zinc-600">
                      Single class drop-in
                    </div>
                  </div>
                  <div className="text-2xl">💳</div>
                </div>
              </button>
            </div>

            <div className="mt-6 flex gap-3">
              <Button variant="secondary" className="flex-1" onClick={() => setBookingStep(1)}>
                Back
              </Button>
              <Button className="flex-1" onClick={() => setBookingStep(3)}>
                Continue
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Confirm */}
        {bookingStep === 3 && (
          <div>
            <h3 className="mb-4 text-lg font-bold">Confirm booking</h3>
            
            <BookingSummaryCard
              studio="Flow House Studio"
              classType="Vinyasa Flow with Sarah Chen"
              date="Mon, Feb 12"
              time="19:00 - 20:00"
              price="1 credit"
              credits={true}
            />

            <div className="mt-6 rounded-xl bg-zinc-50 p-4 text-sm text-zinc-600">
              <div className="font-semibold text-zinc-900">Cancellation policy</div>
              <p className="mt-1">
                Free cancellation up to 12 hours before class. Late
                cancellations will forfeit your credit.
              </p>
            </div>

            <div className="mt-6 flex gap-3">
              <Button variant="secondary" className="flex-1" onClick={() => setBookingStep(2)}>
                Back
              </Button>
              <Button className="flex-1">
                Confirm booking
              </Button>
            </div>
          </div>
        )}
      </PolaroidModal>

      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-zinc-900">
            Booking Flow Demo
          </h1>
          <p className="mt-2 text-zinc-600">
            Click to reopen the booking modal
          </p>
          <Button className="mt-4" onClick={() => {
            setModalOpen(true);
            setBookingStep(1);
          }}>
            Open Booking Modal
          </Button>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// MAIN DEMO APP
// ==========================================

export default function ZeeFrameUIKit() {
  const [currentScreen, setCurrentScreen] = useState("home");

  return (
    <div className="font-sans antialiased">
      {/* Screen selector */}
      <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2">
        <div className="flex gap-2 rounded-full border border-zinc-200 bg-white/90 p-2 shadow-lg backdrop-blur">
          <button
            onClick={() => setCurrentScreen("home")}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              currentScreen === "home"
                ? "bg-gradient-to-br from-sky-400 via-teal-400 to-lime-300 text-zinc-900"
                : "text-zinc-600 hover:bg-zinc-100"
            }`}
          >
            Home
          </button>
          <button
            onClick={() => setCurrentScreen("studio")}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              currentScreen === "studio"
                ? "bg-gradient-to-br from-sky-400 via-teal-400 to-lime-300 text-zinc-900"
                : "text-zinc-600 hover:bg-zinc-100"
            }`}
          >
            Studio
          </button>
          <button
            onClick={() => setCurrentScreen("booking")}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
              currentScreen === "booking"
                ? "bg-gradient-to-br from-sky-400 via-teal-400 to-lime-300 text-zinc-900"
                : "text-zinc-600 hover:bg-zinc-100"
            }`}
          >
            Booking
          </button>
        </div>
      </div>

      {/* Render current screen */}
      {currentScreen === "home" && <DemoHome />}
      {currentScreen === "studio" && <DemoStudioDetail />}
      {currentScreen === "booking" && <DemoBookingFlow />}
    </div>
  );
}
