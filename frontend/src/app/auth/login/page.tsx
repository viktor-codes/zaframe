"use client";

import { useState } from "react";
import Link from "next/link";
import { Button, Card, Input } from "@/components/ui";
import { Alert } from "@/components/ui";
import { requestMagicLink } from "@/lib/api/auth";
import { getUserFacingApiMessage } from "@/lib/api";

export default function LoginPage() {
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
      setError(getUserFacingApiMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-6">
        <Card className="w-full max-w-md">
          <Alert variant="success" title="Check your email">
            If an account exists for {email}, you will receive a link to sign
            in. The link expires in 15 minutes.
          </Alert>
          <p className="mt-4 text-sm text-neutral-600">
            Didn&apos;t receive the email?{" "}
            <button
              type="button"
              onClick={() => {
                setSuccess(false);
              }}
              className="font-medium text-primary hover:text-primary-dark"
            >
              Try again
            </button>
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 p-6">
      <Card className="w-full max-w-md">
        <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
          Sign in
        </h1>
        <p className="mb-6 text-neutral-600">
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

        <p className="mt-6 text-center text-sm text-neutral-500">
          <Link href="/" className="text-primary hover:text-primary-dark">
            ← Back to home
          </Link>
        </p>
      </Card>
    </div>
  );
}
