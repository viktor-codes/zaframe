import Link from "next/link";

interface LegalLinksProps {
  className?: string;
}

/** Minimal Privacy / Cookies links for account and public chrome. */
export function LegalLinks({ className = "" }: LegalLinksProps) {
  return (
    <nav
      aria-label="Legal"
      className={`flex flex-wrap gap-x-4 gap-y-1 text-xs text-neutral-500 ${className}`}
      data-testid="legal-links"
    >
      <Link href="/privacy" className="hover:text-neutral-800 hover:underline">
        Privacy
      </Link>
      <Link href="/cookies" className="hover:text-neutral-800 hover:underline">
        Cookies
      </Link>
    </nav>
  );
}
