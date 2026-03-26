"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { verifyMagicLink } from "@/lib/api/auth";
import { getUserFacingApiMessage } from "@/lib/api";
import { Alert } from "@/components/ui";
import { Skeleton } from "@/components/ui";

/** Dedupe verify in React Strict Mode (dev): second effect must not call the API again. */
const verifyInFlight = new Set<string>();

function VerifyContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading",
  );
  const [errorMessage, setErrorMessage] = useState<string>("");

  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) return;

    if (verifyInFlight.has(token)) {
      return;
    }
    verifyInFlight.add(token);

    verifyMagicLink(token)
      .then((data) => {
        login(data.access_token, data.user);
        setStatus("success");
        router.replace("/");
      })
      .catch((err) => {
        setStatus("error");
        setErrorMessage(getUserFacingApiMessage(err));
      })
      .finally(() => {
        verifyInFlight.delete(token);
      });
  }, [token, login, router]);

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-6">
        <div className="w-full max-w-md">
          <Alert variant="error" title="Verification failed">
            Missing token. Please use the link from your email.
          </Alert>
          <a
            href="/auth/login"
            className="mt-6 block text-center font-medium text-primary hover:text-primary-dark"
          >
            Request a new magic link
          </a>
        </div>
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-6">
        <div className="w-full max-w-md text-center">
          <Skeleton className="mx-auto mb-4 h-12 w-48" />
          <Skeleton className="mb-2 h-4 w-full" />
          <Skeleton className="mx-auto h-4 w-3/4" />
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-6">
        <div className="w-full max-w-md">
          <Alert variant="error" title="Verification failed">
            {errorMessage}
          </Alert>
          <a
            href="/auth/login"
            className="mt-6 block text-center font-medium text-primary hover:text-primary-dark"
          >
            Request a new magic link
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-6">
      <div className="w-full max-w-md text-center">
        <p className="text-neutral-600">Redirecting...</p>
      </div>
    </div>
  );
}

export default function VerifyPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-6">
          <Skeleton className="h-12 w-48" />
        </div>
      }
    >
      <VerifyContent />
    </Suspense>
  );
}
