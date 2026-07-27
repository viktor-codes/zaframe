"use client";

import { useMutation } from "@tanstack/react-query";
import { getCurrentUserExport } from "@shared/api";
import { toast } from "@shared/ui";

function downloadJson(filename: string, data: unknown): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

/**
 * Fetch GDPR export and trigger a JSON file download.
 */
export function useExportAccountData() {
  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: () => getCurrentUserExport(),
    onSuccess: (data) => {
      const stamp = new Date().toISOString().slice(0, 10);
      downloadJson(`zeeframe-data-export-${stamp}.json`, data);
      toast.success("Your data download started");
    },
  });

  return {
    exportAccountData: mutation.mutate,
    isExporting: mutation.isPending,
  };
}
