"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AuthProvider } from "@shared/auth";
import { createAppQueryClient } from "@shared/lib/query-client";
import { ErrorBoundary } from "@shared/ui";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => createAppQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ErrorBoundary>{children}</ErrorBoundary>
      </AuthProvider>
    </QueryClientProvider>
  );
}
