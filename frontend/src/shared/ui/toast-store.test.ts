import { afterEach, describe, expect, it, vi } from "vitest";

import { toast, useToastStore } from "./toast-store";

afterEach(() => {
  useToastStore.getState().clear();
  vi.useRealTimers();
});

describe("toast store", () => {
  it("pushes and dismisses toasts", () => {
    const id = toast.error("Payment failed");
    expect(useToastStore.getState().toasts).toHaveLength(1);
    expect(useToastStore.getState().toasts[0]).toMatchObject({
      id,
      message: "Payment failed",
      tone: "error",
    });
    toast.dismiss(id);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("keeps only the latest three toasts", () => {
    toast.info("1");
    toast.info("2");
    toast.info("3");
    toast.info("4");
    expect(useToastStore.getState().toasts.map((t) => t.message)).toEqual([
      "2",
      "3",
      "4",
    ]);
  });

  it("auto-dismisses after the duration", () => {
    vi.useFakeTimers();
    const id = toast.success("Saved", { durationMs: 1000 });
    expect(useToastStore.getState().toasts).toHaveLength(1);
    vi.advanceTimersByTime(1000);
    expect(useToastStore.getState().toasts.find((t) => t.id === id)).toBe(
      undefined,
    );
  });
});
