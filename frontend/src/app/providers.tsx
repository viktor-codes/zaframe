"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AuthProvider } from "@shared/auth";
import { createAppQueryClient } from "@shared/lib/query-client";
import { Toaster, toastApiError } from "@shared/ui";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() =>
    createAppQueryClient({
      onMutationToastError: toastApiError,
    }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        {children}
        <Toaster />
      </AuthProvider>
    </QueryClientProvider>
  );
}
