"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

export type NavLink = { name: string; href: string };

export const MobileMenu = ({
  isOpen,
  links,
  onClose,
}: {
  isOpen: boolean;
  links: NavLink[];
  onClose: () => void;
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const cornerClass = "absolute w-6 h-6 border-black border-2";

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            key="curtain"
            initial={{ y: "-100%" }}
            animate={{ y: 0 }}
            exit={{ y: "-100%" }}
            transition={{
              duration: 0.3,
              ease: "linear",
            }}
            className="fixed left-0 right-0 top-25 z-30 flex h-[calc(90vh-100px)] flex-col bg-white/90 backdrop-blur-2xl md:hidden"
          />
          <motion.div
            initial={{ y: "-100%" }}
            animate={{ y: 0 }}
            exit={{ y: "-100%" }}
            transition={{ duration: 0.3, ease: "linear" }}
            className="fixed inset-x-0 z-30 flex h-[calc(90vh-100px)] flex-col bg-white/70 backdrop-blur-2xl md:hidden"
          >
            <div className="absolute inset-4 pointer-events-none">
              <motion.div
                initial={{ opacity: 0, x: 20, y: 20 }}
                animate={{ opacity: 1, x: 0, y: 0 }}
                transition={{ delay: 0.3 }}
                className={`${cornerClass} top-0 left-0 border-r-0 border-b-0`}
              />
              <motion.div
                initial={{ opacity: 0, x: -20, y: 20 }}
                animate={{ opacity: 1, x: 0, y: 0 }}
                transition={{ delay: 0.3 }}
                className={`${cornerClass} top-0 right-0 border-l-0 border-b-0`}
              />
              <motion.div
                initial={{ opacity: 0, x: 20, y: -20 }}
                animate={{ opacity: 1, x: 0, y: 0 }}
                transition={{ delay: 0.3 }}
                className={`${cornerClass} bottom-0 left-0 border-r-0 border-t-0`}
              />
              <motion.div
                initial={{ opacity: 0, x: -20, y: -20 }}
                animate={{ opacity: 1, x: 0, y: 0 }}
                transition={{ delay: 0.3 }}
                className={`${cornerClass} bottom-0 right-0 border-l-0 border-t-0`}
              />
            </div>
            <div className="flex flex-1 flex-col px-8 py-10">
              <nav className="flex flex-col gap-2">
                {links.map((link, i) => (
                  <motion.a
                    key={link.name}
                    href={link.href}
                    onClick={(e) => {
                      if (link.href.startsWith("#")) {
                        e.preventDefault();
                        document
                          .querySelector(link.href)
                          ?.scrollIntoView({ behavior: "smooth" });
                      }
                      onClose();
                    }}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2, ease: "easeInOut" }}
                    className="flex items-center justify-between border-b border-zinc-100 py-6 text-black active:bg-zinc-50"
                  >
                    <span className="text-4xl font-light tracking-tight">
                      {link.name}
                    </span>
                    <span className="text-zinc-400">→</span>
                  </motion.a>
                ))}
              </nav>

              <div className="mt-auto pb-10">
                <Link
                  href="#signin"
                  onClick={onClose}
                  className="block w-full rounded-lg bg-zinc-900 py-5 text-center text-lg font-medium text-white shadow-xl"
                >
                  Sign in
                </Link>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
