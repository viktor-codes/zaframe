'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const MOMENTS = [
  { id: 1, img: "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b", title: "Morning Flow" },
  { id: 2, img: "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad", title: "Urban Dance" },
  { id: 3, img: "https://images.unsplash.com/photo-1518611012118-2969c6370238", title: "Core Pilates" },
  { id: 4, img: "https://images.unsplash.com/photo-1552072092-7f9b8d63efcb", title: "Yoga Stretch" },
];

export const AutoShuffleDeck = () => {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % MOMENTS.map(m => m.id).length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative flex h-[600px] w-full items-center justify-center pt-20">
      <div className="relative h-[400px] w-full max-w-2xl">
        {MOMENTS.map((card, index) => {
          const isActive = index === activeIndex;
          
          // Расчет угла для веера: например от -20 до +20 градусов
          const totalCards = MOMENTS.length;
          const angleStep = 40 / (totalCards - 1);
          const baseRotation = -20 + index * angleStep;

          return (
            <motion.div
              key={card.id}
              initial={false}
              animate={{
                // Если карточка активна — она вылетает вперед и центрируется
                // Если нет — стоит в веере
                rotate: isActive ? 0 : baseRotation,
                x: isActive ? 0 : (index - (totalCards - 1) / 2) * 45, // Разлет по горизонтали
                y: isActive ? -80 : Math.abs(index - (totalCards - 1) / 2) * 15, // Дуга веера
                scale: isActive ? 1.1 : 0.9,
                zIndex: isActive ? 50 : index,
              }}
              transition={{
                type: "spring",
                stiffness: 150,
                damping: 20
              }}
              className="absolute left-1/2 top-0 -translate-x-1/2"
            >
              {/* Polaroid UI из твоего кита */}
              <div className={`
                relative w-[260px] rounded-[20px] bg-white p-3 pb-8 shadow-2xl transition-shadow duration-500
                ${isActive ? 'shadow-teal-500/20' : 'shadow-black/5'}
              `}>
                <div className="relative aspect-[4/5] overflow-hidden rounded-[12px] bg-zinc-100">
                  <motion.img 
                    animate={{ scale: isActive ? 1.05 : 1 }}
                    src={card.img} 
                    className="h-full w-full object-cover" 
                  />
                  {/* Легкий отблеск при активации */}
                  <AnimatePresence>
                    {isActive && (
                      <motion.div 
                        initial={{ x: '-100%' }}
                        animate={{ x: '200%' }}
                        transition={{ duration: 0.8 }}
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                      />
                    )}
                  </AnimatePresence>
                </div>
                
                <div className="mt-4 flex flex-col items-center gap-1">
                  <div className="h-1 w-8 rounded-full bg-zinc-100" />
                  <span className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400">
                    {card.title}
                  </span>
                </div>

                {/* Имитация "видоискателя" на активной карточке */}
                {isActive && (
                  <>
                    <div className="absolute top-2 left-2 w-4 h-4 border-t border-l border-teal-500" />
                    <div className="absolute top-2 right-2 w-4 h-4 border-t border-r border-teal-500" />
                  </>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default AutoShuffleDeck;