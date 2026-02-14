"use client";

import { motion } from "framer-motion";
import Image from "next/image";

const LOGO_PARTNERS = [
  { src: "/logos/logo-acme.png", alt: "Acme Fitness" },
  { src: "/logos/logo-pulse.png", alt: "Pulse Yoga" },
  { src: "/logos/logo-echo.png", alt: "Echo Boxing" },
  { src: "/logos/logo-celestial.png", alt: "Celestial Pilates" },
  { src: "/logos/logo-apex.png", alt: "Apex HIIT" },
  { src: "/logos/logo-quantum.png", alt: "Quantum Studio" },
];

export const LogoTicker = () => {
  return (
    <div className="py-12 bg-zinc-50">
      <div className="container mx-auto">
        <div className="flex overflow-hidden [mask-image:linear_to_right,transparent,black_20%,black_80%,transparent)]">
          <motion.div
            className="flex gap-20 flex-none pr-20"
            animate={{
              translateX: "-50%",
            }}
            transition={{
              duration: 25, // Элегантная скорость
              repeat: Infinity,
              ease: "linear",
              repeatType: "loop",
            }}
          >
            {/* Первый набор логотипов */}
            {LOGO_PARTNERS.map((logo, index) => (
              <Image
                width={100}
                height={100}
                key={`first-${index}`}
                src={logo.src}
                alt={logo.alt}
                className="h-9 w-auto opacity-40 grayscale hover:opacity-100 hover:grayscale-0 transition-all duration-300"
              />
            ))}

            {/* Второй набор логотипов для бесконечного цикла */}
            {LOGO_PARTNERS.map((logo, index) => (
              <Image
                width={100}
                height={100}
                key={`second-${index}`}
                src={logo.src}
                alt={logo.alt}
                className="h-9 w-auto opacity-40 grayscale hover:opacity-100 hover:grayscale-0 transition-all duration-300"
              />
            ))}
          </motion.div>
        </div>
      </div>
    </div>
  );
};
