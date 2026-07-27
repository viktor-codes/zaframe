import Link from "next/link";

import { CreateStudioForm } from "@features/manage-studio";
import { Card } from "@shared/ui/card";

export default function NewStudioPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
      <Link
        href="/dashboard"
        className="mb-6 inline-block text-sm font-medium text-primary hover:text-primary-dark"
      >
        ← Back to dashboard
      </Link>
      <h1 className="text-secondary mb-2 font-display text-2xl font-bold">
        Create studio
      </h1>
      <p className="mb-6 text-sm text-neutral-600">
        Start with a name and timezone. You can finish slug and city next.
      </p>
      <Card className="p-6">
        <CreateStudioForm />
      </Card>
    </div>
  );
}
