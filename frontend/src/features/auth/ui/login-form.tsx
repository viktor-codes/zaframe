"use client";

import { Suspense } from "react";
import Link from "next/link";
import { Alert, Button, Card, Input, Skeleton } from "@shared/ui";
import { useOtpLogin } from "../model/use-otp-login";

function LoginFormInner() {
  const otp = useOtpLogin();

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-6">
      <Card className="w-full max-w-md">
        {otp.step === "request" ? (
          <>
            <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
              Sign in
            </h1>
            <p className="mb-6 text-neutral-600">
              Enter your email and we&apos;ll send you a 6-digit code.
            </p>

            <form onSubmit={otp.submitRequest} className="space-y-4">
              {otp.error && (
                <Alert variant="error" title="Something went wrong">
                  {otp.error}
                </Alert>
              )}

              <Input
                label="Full name"
                type="text"
                placeholder="John Doe"
                value={otp.name}
                onChange={(e) => otp.setName(e.target.value)}
                required
                minLength={1}
                maxLength={100}
                autoComplete="name"
              />
              <Input
                label="Email"
                type="email"
                placeholder="john@example.com"
                value={otp.email}
                onChange={(e) => otp.setEmail(e.target.value)}
                required
                autoComplete="email"
              />

              <Button type="submit" fullWidth isLoading={otp.isSubmitting}>
                Send code
              </Button>
            </form>
          </>
        ) : (
          <>
            <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
              Enter your code
            </h1>
            <p className="mb-6 text-neutral-600">
              We sent a 6-digit code to{" "}
              <span className="font-medium text-neutral-800">{otp.email}</span>.
            </p>

            <form onSubmit={otp.submitCode} className="space-y-4">
              {otp.error && (
                <Alert variant="error" title="Something went wrong">
                  {otp.error}
                </Alert>
              )}

              <Input
                label="Verification code"
                type="text"
                inputMode="numeric"
                placeholder="123456"
                value={otp.code}
                onChange={(e) =>
                  otp.setCode(e.target.value.replace(/\D/g, "").slice(0, 6))
                }
                required
                autoComplete="one-time-code"
                autoFocus
              />

              <Button type="submit" fullWidth isLoading={otp.isSubmitting}>
                Verify &amp; continue
              </Button>
            </form>

            <div className="mt-4 flex items-center justify-between text-sm">
              <button
                type="button"
                onClick={otp.resend}
                disabled={otp.isSubmitting}
                className="font-medium text-primary hover:text-primary-dark disabled:opacity-50"
              >
                Resend code
              </button>
              <button
                type="button"
                onClick={otp.editEmail}
                className="text-neutral-500 hover:text-neutral-700"
              >
                Use a different email
              </button>
            </div>
          </>
        )}

        <p className="mt-6 text-center text-sm text-neutral-500">
          <Link href="/" className="text-primary hover:text-primary-dark">
            ← Back to home
          </Link>
        </p>
      </Card>
    </div>
  );
}

function LoginFormFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-6">
      <Card className="w-full max-w-md space-y-4">
        <Skeleton className="h-9 w-40" />
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-11 w-full" />
        <Skeleton className="h-11 w-full" />
      </Card>
    </div>
  );
}

export function LoginForm() {
  return (
    <Suspense fallback={<LoginFormFallback />}>
      <LoginFormInner />
    </Suspense>
  );
}
