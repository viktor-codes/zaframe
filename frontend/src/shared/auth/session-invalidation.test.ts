import { afterEach, describe, expect, it } from "vitest";

import {
  notifyAuthSessionInvalidated,
  resolveAuthUserFromQuery,
  setAuthSessionInvalidatedHandler,
} from "./session-invalidation";

describe("resolveAuthUserFromQuery", () => {
  it("returns null when the auth query is in error (no ghost session)", () => {
    expect(
      resolveAuthUserFromQuery({ id: 1, email: "a@b.c" }, true),
    ).toBeNull();
  });

  it("returns the user when the query succeeded", () => {
    const user = { id: 1, email: "a@b.c" };
    expect(resolveAuthUserFromQuery(user, false)).toEqual(user);
  });

  it("returns null when there is no data yet", () => {
    expect(resolveAuthUserFromQuery(undefined, false)).toBeNull();
  });
});

describe("notifyAuthSessionInvalidated", () => {
  afterEach(() => {
    setAuthSessionInvalidatedHandler(null);
  });

  it("invokes the registered handler", () => {
    let called = 0;
    setAuthSessionInvalidatedHandler(() => {
      called += 1;
    });
    notifyAuthSessionInvalidated();
    expect(called).toBe(1);
  });

  it("is a no-op when no handler is registered", () => {
    expect(() => notifyAuthSessionInvalidated()).not.toThrow();
  });
});
