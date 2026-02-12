"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { verifyMagicLink } from "@/lib/api/auth";
import { ApiError } from "@/lib/api";
import { Alert } from "@/components/ui";
import { Skeleton } from "@/components/ui";

function VerifyContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [errorMessage, setErrorMessage] = useState<string>("");

  const token = searchParams.get("token");

  if (!token) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full">
          <Alert variant="error" title="Verification failed">
            Missing token. Please use the link from your email.
          </Alert>
          <a
            href="/auth/login"
            className="block text-center mt-6 text-primary hover:text-primary-dark font-medium"
          >
            Request a new magic link
          </a>
        </div>
      </div>
    );
  }

  useEffect(() => {
    verifyMagicLink(token)
      .then((data) => {
        login(data.access_token, data.refresh_token, data.user);
        setStatus("success");
        router.replace("/");
      })
      .catch((err) => {
        setStatus("error");
        const detail =
          err instanceof ApiError
            ? typeof err.body === "object" && err.body && "detail" in err.body
              ? String((err.body as { detail: unknown }).detail)
              : err.message
            : "Link is invalid or expired. Please request a new one.";
        setErrorMessage(detail);
      });
  }, [token, login, router]);

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center">
          <Skeleton className="h-12 w-48 mx-auto mb-4" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4 mx-auto" />
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full">
          <Alert variant="error" title="Verification failed">
            {errorMessage}
          </Alert>
          <a
            href="/auth/login"
            className="block text-center mt-6 text-primary hover:text-primary-dark font-medium"
          >
            Request a new magic link
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center">
        <p className="text-neutral-600">Redirecting...</p>
      </div>
    </div>
  );
}

export default function VerifyPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
          <Skeleton className="h-12 w-48" />
        </div>
      }
    >
      <VerifyContent />
    </Suspense>
  );
}
