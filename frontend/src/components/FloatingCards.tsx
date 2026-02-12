"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

const FloatingCards = () => {
  const [cards, setCards] = useState([
    { id: 0, rotation: -12, img: "/yoga.webp", label: "Yoga Flow" },
    { id: 1, rotation: 2, img: "/cont.webp", label: "Contemporary" },
    { id: 2, rotation: 10, img: "hip-hop.webp", label: "hip-hop" },
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCards((prevCards) => {
        const [first, ...rest] = prevCards;
        return [...rest, first]; // Первая уходит в конец
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Определяем X-позиции на основе текущего индекса в массиве
  const getXPosition = (index: number) => {
    if (index === 0) return -220; // Слева
    if (index === 1) return 0; // Центр
    return 220; // Справа
  };

  return (
    <div className="relative h-[550px] w-full max-w-3xl flex items-center justify-center">
      <AnimatePresence mode="popLayout">
        {cards.map((card, index) => {
          // В этой логике "активной" логично считать центральную карточку (индекс 1)
          // или ту, что была первой. Давай сделаем центральную (индекс 1) акцентной.
          const isActive = index === 1;

          return (
            <motion.div
              key={card.id} // Важно: key привязан к id, а не к индексу
              layout // Магия плавного перемещения
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{
                opacity: 1,
                scale: isActive ? 1.1 : 0.95,
                rotate: card.rotation,
                x: getXPosition(index),
                y: isActive ? [0, -20, 0] : [0, -10, 0],
                zIndex: isActive ? 10 : index,
              }}
              exit={{ opacity: 0, scale: 0.5, transition: { duration: 0.4 } }}
              transition={{
                layout: { type: "spring", stiffness: 200, damping: 25 },
                scale: { duration: 0.4 },
                y: {
                  duration: isActive ? 3 : 4,
                  repeat: Infinity,
                  ease: "easeInOut",
                },
              }}
              className={`absolute left-1/2 -translate-x-1/2 rounded-lg bg-white p-3 shadow-2xl border transition-colors duration-700 ${
                isActive
                  ? "border-teal-400/50 shadow-teal-500/15"
                  : "border-zinc-100 shadow-black/5"
              }`}
              style={{ width: "280px" }}
            >
              {/* Контейнер изображения */}
              <div className="relative aspect-9/10 overflow-hidden rounded-lg bg-zinc-100">
                <motion.img
                  animate={{ scale: isActive ? 1.15 : 1 }}
                  transition={{ duration: 2 }}
                  src={card.img}
                  alt={card.label}
                  className="h-full w-full object-cover"
                />

                {isActive && (
                  <motion.div
                    initial={{ x: "-150%" }}
                    animate={{ x: "150%" }}
                    transition={{
                      duration: 1.5,
                      repeat: Infinity,
                      repeatDelay: 1,
                    }}
                    className="absolute inset-0 bg-linear-to-r from-transparent via-white/40 to-transparent -skew-x-12"
                  />
                )}

                <div
                  className={`absolute bottom-3 left-3 rounded-lg px-2.5 py-1 text-[10px] font-black uppercase tracking-widest transition-all duration-500 ${
                    isActive
                      ? "bg-teal-400 text-zinc-900 shadow-lg shadow-teal-500/50"
                      : "bg-white/90 text-zinc-600"
                  }`}
                >
                  {card.label}
                </div>
              </div>

              {/* Детали карточки */}
              <div className="mt-5 px-1 flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <div
                    className={`h-1.5 w-16 rounded-lg transition-colors duration-500 ${isActive ? "bg-teal-200" : "bg-zinc-100"}`}
                  />
                  <div className="h-1.5 w-8 rounded-lg bg-zinc-50" />
                </div>
                <div className="text-[9px] font-mono text-zinc-400 tracking-wider flex justify-between uppercase">
                  <span>Moment 00{card.id + 1}</span>
                  <span className={isActive ? "text-teal-500 font-bold" : ""}>
                    {isActive ? "● Live" : "Static"}
                  </span>
                </div>
              </div>

              {/* Уголки видоискателя */}
              {isActive && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="absolute inset-0 pointer-events-none"
                >
                  <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-teal-500/60 rounded-tl-xl" />
                  <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-teal-500/60 rounded-tr-xl" />
                  <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-teal-500/60 rounded-bl-xl" />
                  <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-teal-500/60 rounded-br-xl" />
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};

export default FloatingCards;
