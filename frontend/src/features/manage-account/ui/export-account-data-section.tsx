"use client";

import { Button } from "@shared/ui";
import { useExportAccountData } from "../model/use-export-account-data";

/**
 * Profile action: download GDPR DSAR JSON from GET /me/export.
 */
export function ExportAccountDataSection() {
  const { exportAccountData, isExporting } = useExportAccountData();

  return (
    <div
      className="rounded-xl border border-zinc-200 bg-white p-4"
      data-testid="export-account-section"
    >
      <h2 className="text-sm font-semibold text-zinc-900">Download my data</h2>
      <p className="mt-1 mb-3 text-xs text-zinc-500">
        Get a JSON copy of your profile, bookings, orders, and payments.
      </p>
      <Button
        type="button"
        variant="outline"
        size="sm"
        isLoading={isExporting}
        onClick={() => exportAccountData()}
        data-testid="export-account-button"
      >
        Download my data
      </Button>
    </div>
  );
}
