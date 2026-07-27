"use client";

import { useState } from "react";
import { Button } from "@shared/ui";
import { useDeleteAccount } from "../model/use-delete-account";

/**
 * Profile danger zone: soft-delete with inline confirm (no modal lib).
 */
export function DeleteAccountSection() {
  const [showConfirm, setShowConfirm] = useState(false);
  const { deleteAccount, isDeleting } = useDeleteAccount();

  if (showConfirm) {
    return (
      <div
        className="rounded-xl border border-red-200 bg-red-50 p-4"
        data-testid="delete-account-confirm"
      >
        <p className="mb-1 text-sm font-medium text-red-800">
          Delete your account? This cannot be undone.
        </p>
        <p className="mb-3 text-xs text-red-700/80">
          Bookings and payment history are kept for studio records. You will be
          signed out immediately.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="danger"
            size="sm"
            isLoading={isDeleting}
            onClick={() => deleteAccount()}
            data-testid="confirm-delete-account"
          >
            Yes, delete my account
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isDeleting}
            onClick={() => setShowConfirm(false)}
            data-testid="cancel-delete-account"
          >
            Keep my account
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="rounded-xl border border-zinc-200 bg-white p-4"
      data-testid="delete-account-section"
    >
      <h2 className="text-sm font-semibold text-zinc-900">Delete account</h2>
      <p className="mt-1 mb-3 text-xs text-zinc-500">
        Permanently close your ZeeFrame login. Studios keep booking history.
      </p>
      <Button
        type="button"
        variant="danger"
        size="sm"
        onClick={() => setShowConfirm(true)}
        data-testid="delete-account-button"
      >
        Delete my account
      </Button>
    </div>
  );
}
