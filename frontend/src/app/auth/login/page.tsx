"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, Card, Input } from "@/components/ui";
import { Alert } from "@/components/ui";
import { requestMagicLink } from "@/lib/api/auth";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await requestMagicLink({ email, name });
      setSuccess(true);
    } catch (err) {
      const detail =
        err instanceof ApiError
          ? typeof err.body === "object" && err.body && "detail" in err.body
            ? String((err.body as { detail: unknown }).detail)
            : err.message
          : "Something went wrong. Please try again.";
      setError(detail);
    } finally {
      setIsLoading(false);
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <Card className="max-w-md w-full">
          <Alert variant="success" title="Check your email">
            If an account exists for {email}, you will receive a link to sign in.
            The link expires in 15 minutes.
          </Alert>
          <p className="text-sm text-neutral-600 mt-4">
            Didn&apos;t receive the email?{" "}
            <button
              type="button"
              onClick={() => {
                setSuccess(false);
              }}
              className="text-primary hover:text-primary-dark font-medium"
            >
              Try again
            </button>
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
      <Card className="max-w-md w-full">
        <h1 className="font-display font-bold text-3xl text-secondary mb-2">
          Sign in
        </h1>
        <p className="text-neutral-600 mb-6">
          Enter your email and we&apos;ll send you a link to sign in.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="error" title="Error">
              {error}
            </Alert>
          )}

          <Input
            label="Full Name"
            type="text"
            placeholder="John Doe"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            minLength={1}
            maxLength={100}
          />
          <Input
            label="Email"
            type="email"
            placeholder="john@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <Button type="submit" fullWidth isLoading={isLoading}>
            Send magic link
          </Button>
        </form>

        <p className="text-sm text-neutral-500 mt-6 text-center">
          <Link href="/" className="text-primary hover:text-primary-dark">
            ← Back to home
          </Link>
        </p>
      </Card>
    </div>
  );
}
