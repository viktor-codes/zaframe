"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";

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

  const router = useRouter();

  const handleLinkClick = (
    e: React.MouseEvent<HTMLAnchorElement>,
    href: string,
  ) => {
    e.preventDefault();
    const isAnchor = href.includes("#");
    const isInternal = href.startsWith("/");

    // 1. Сначала инициируем закрытие меню
    onClose();

    // 2. Ждем завершения анимации (300ms + запас 50ms)
    setTimeout(() => {
      if (isAnchor) {
        const id = href.split("#")[1];
        const targetElement = document.getElementById(id);

        if (targetElement) {
          targetElement.scrollIntoView({ behavior: "smooth" });
        } else {
          // Если якорь на другой странице (напр. /#moments)
          router.push(href);
        }
      } else {
        // Обычный переход на другую страницу
        router.push(href);
      }
    }, 350);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-x-0 z-50 flex h-[calc(100svh-100px)] flex-col bg-white will-change-transform md:hidden"
          >
            <div className="pointer-events-none absolute inset-4">
              {/* Top Left */}
              <div
                className={`${cornerClass} top-0 left-0 animate-corner-tl border-r-0 border-b-0 opacity-0`}
              />

              {/* Top Right */}
              <div
                className={`${cornerClass} top-0 right-0 animate-corner-tr border-b-0 border-l-0 opacity-0`}
              />

              {/* Bottom Left */}
              <div
                className={`${cornerClass} bottom-0 left-0 animate-corner-bl border-t-0 border-r-0 opacity-0`}
              />

              {/* Bottom Right */}
              <div
                className={`${cornerClass} right-0 bottom-0 animate-corner-br border-t-0 border-l-0 opacity-0`}
              />
            </div>
            <div className="flex flex-1 flex-col px-8 py-10">
              <nav className="flex flex-col gap-2">
                {links.map((link, i) => (
                  <a
                    key={link.name}
                    href={link.href}
                    onClick={(e) => handleLinkClick(e, link.href)}
                    className="flex items-center justify-between border-b border-zinc-100 py-6 text-black active:bg-zinc-50"
                  >
                    <span className="text-4xl font-light tracking-tight">
                      {link.name}
                    </span>
                    <span className="text-zinc-400">→</span>
                  </a>
                ))}
              </nav>

              <div className="mt-auto pb-10">
                <Link
                  href="/auth/login"
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
