import Link from "next/link";
import { Button } from "@/components/ui";

export default function HomePage() {
  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <section className="mb-16">
        <h1 className="font-display font-bold text-5xl text-secondary mb-4">
          Book Your Session
        </h1>
        <p className="text-neutral-700 mb-6 max-w-xl">
          Professional photography and video studio services with instant
          booking. Choose your preferred date and time, and we&apos;ll capture
          your perfect moment.
        </p>
        <div className="flex flex-wrap gap-4">
          <Button asChild>
            <Link href="/studios">Book Now</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/studios">View All Studios</Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
